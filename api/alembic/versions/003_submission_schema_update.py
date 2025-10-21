"""
Submission schema update: add missing person fields, enforce enums (gender: male/female; race: updated set), add 'found' status, replace age->dob (Postgres-safe)

Revision ID: 003_submission_schema_update
Revises: 002_local_auth
Create Date: 2025-10-15
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_submission_schema_update'
down_revision = '002_local_auth'
branch_labels = None
depends_on = None


def _colnames(bind, table: str):
    insp = sa.inspect(bind)
    return {c['name'] for c in insp.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    cols = _colnames(bind, 'submission')

    # --- Enums (Postgres-safe, idempotent) ---
    if dialect == 'postgresql':
        # Create enums with duplicate_object protection to avoid aborting the TX
        op.execute(
            """
            DO $$ BEGIN
              CREATE TYPE mp_gender_enum AS ENUM ('male','female');
            EXCEPTION WHEN duplicate_object THEN NULL; END $$;
            """
        )
        op.execute(
            """
            DO $$ BEGIN
              CREATE TYPE submission_status_enum AS ENUM ('pending','published','rejected','found_alive', 'found_dead');
            EXCEPTION WHEN duplicate_object THEN NULL; END $$;
            """
        )
        op.execute(
            """
            DO $$ BEGIN
              CREATE TYPE race_enum AS ENUM ('black_african','coloured','white','asian_or_indian','other');
            EXCEPTION WHEN duplicate_object THEN NULL; END $$;
            """
        )
        op.execute(
            """
            DO $$ BEGIN
              CREATE TYPE province_enum AS ENUM (
                'eastern_cape','free_state','gauteng','kwazulu_natal','limpopo','mpumalanga','north_west','northern_cape','western_cape'
              );
            EXCEPTION WHEN duplicate_object THEN NULL; END $$;
            """
        )


    # --- Columns (add if missing) ---
    if 'full_name' not in cols:
        op.add_column('submission', sa.Column('full_name', sa.String(length=255), nullable=True))

    # Gender column
    if 'gender' not in cols:
        if dialect == 'postgresql':
            op.add_column('submission', sa.Column('gender', sa.Enum(name='mp_gender_enum', create_type=False), nullable=True))
        else:
            op.add_column('submission', sa.Column('gender', sa.Enum('male', 'female', name='mp_gender_enum'), nullable=True))

    if 'description' not in cols:
        op.add_column('submission', sa.Column('description', sa.Text(), nullable=True))

    if 'status' not in cols:
        if dialect == 'postgresql':
            op.add_column('submission', sa.Column('status', sa.Enum(name='submission_status_enum', create_type=False), nullable=False, server_default='pending'))
        else:
            op.add_column('submission', sa.Column('status', sa.Enum('pending', 'published', 'rejected', 'found_alive', 'found_dead', name='submission_status_enum'), nullable=False, server_default='pending'))

    if 'last_seen_address' not in cols:
        op.add_column('submission', sa.Column('last_seen_address', sa.String(length=512), nullable=True))
    if 'last_seen_place_id' not in cols:
        op.add_column('submission', sa.Column('last_seen_place_id', sa.String(length=128), nullable=True))
    if 'last_seen_lat' not in cols:
        op.add_column('submission', sa.Column('last_seen_lat', sa.Float(), nullable=True))
    if 'last_seen_lng' not in cols:
        op.add_column('submission', sa.Column('last_seen_lng', sa.Float(), nullable=True))

    if 'images' not in cols:
        op.add_column('submission', sa.Column('images', sa.JSON(), nullable=True))

    if 'dob' not in cols:
        op.add_column('submission', sa.Column('dob', sa.Date(), nullable=True))

    if 'race' not in cols:
        if dialect == 'postgresql':
            op.add_column('submission', sa.Column('race', sa.Enum(name='race_enum', create_type=False), nullable=True))
        else:
            op.add_column('submission', sa.Column('race', sa.Enum('black_african', 'coloured', 'white', 'asian_or_indian', 'other', name='race_enum'), nullable=True))

    if 'height' not in cols:
        op.add_column('submission', sa.Column('height', sa.Float(), nullable=True))
    if 'weight' not in cols:
        op.add_column('submission', sa.Column('weight', sa.Float(), nullable=True))

    if 'province' not in cols:
        if dialect == 'postgresql':
            op.add_column('submission', sa.Column('province', sa.Enum(name='province_enum', create_type=False), nullable=True))
        else:
            op.add_column('submission', sa.Column('province', sa.Enum('eastern_cape', 'free_state', 'gauteng', 'kwazulu_natal', 'limpopo', 'mpumalanga', 'north_west', 'northern_cape', 'western_cape', name='province_enum'), nullable=True))

    # --- Postgres enum migrations (no errors) ---
    if dialect == 'postgresql':
        # Gender: remove 'other' if present without raising
        op.execute(
            """
            DO $$ BEGIN
              IF EXISTS (
                SELECT 1 FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE t.typname = 'mp_gender_enum' AND e.enumlabel = 'other'
              ) THEN
                CREATE TYPE mp_gender_enum_new AS ENUM ('male','female');
                ALTER TABLE submission ALTER COLUMN gender TYPE mp_gender_enum_new USING gender::text::mp_gender_enum_new;
                DROP TYPE mp_gender_enum;
                ALTER TYPE mp_gender_enum_new RENAME TO mp_gender_enum;
              END IF;
            END $$;
            """
        )

        # Race: if old labels exist, migrate via a wide temp enum then narrow to final enum
        op.execute(
            """
            DO $$ BEGIN
              IF EXISTS (
                SELECT 1 FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE t.typname = 'race_enum' AND e.enumlabel IN ('african','asian','indian')
              ) THEN
                -- Create a superset type that includes both old and new labels
                CREATE TYPE race_enum_wide AS ENUM ('african','coloured','indian','white','asian','black_african','asian_or_indian','other');
                -- Move column to wide type
                ALTER TABLE submission ALTER COLUMN race TYPE race_enum_wide USING race::text::race_enum_wide;
                -- Remap values
                UPDATE submission SET race = 'black_african' WHERE race = 'african';
                UPDATE submission SET race = 'asian_or_indian' WHERE race IN ('asian','indian');
                -- Recreate the final type and use it
                CREATE TYPE race_enum_final AS ENUM ('black_african','coloured','white','asian_or_indian','other');
                ALTER TABLE submission ALTER COLUMN race TYPE race_enum_final USING race::text::race_enum_final;
                -- Drop old types and rename final to race_enum
                DROP TYPE IF EXISTS race_enum;
                DROP TYPE race_enum_wide;
                ALTER TYPE race_enum_final RENAME TO race_enum;
              END IF;
            END $$;
            """
        )

        # Province: ensure enum type is applied (no error if already enum)
        op.execute(
            """
            DO $$ BEGIN
              BEGIN
                ALTER TABLE submission ALTER COLUMN province TYPE province_enum USING province::text::province_enum;
              EXCEPTION WHEN others THEN
                -- ignore if already correct type or column missing
                NULL;
              END;
            END $$;
            """
        )

    # Drop legacy age column if present
    if 'age' in cols:
        op.drop_column('submission', 'age')


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Best-effort downgrade: re-add age
    cols = _colnames(bind, 'submission')
    if 'age' not in cols:
        op.add_column('submission', sa.Column('age', sa.Integer(), nullable=True))

    # Drop added columns if present (safe order)
    for col in (
        'province','weight','height','race','dob','images','last_seen_lng','last_seen_lat',
        'last_seen_place_id','last_seen_address','status','description','gender','full_name'):
        cols = _colnames(bind, 'submission')
        if col in cols:
            op.drop_column('submission', col)

    # Attempt to restore old gender enum with 'other' on Postgres
    if dialect == 'postgresql':
        op.execute(
            """
            DO $$ BEGIN
              CREATE TYPE mp_gender_enum_old AS ENUM ('male','female','other');
            EXCEPTION WHEN duplicate_object THEN NULL; END $$;
            """
        )
        op.execute(
            """
            DO $$ BEGIN
              BEGIN
                ALTER TABLE submission ALTER COLUMN gender TYPE mp_gender_enum_old USING gender::text::mp_gender_enum_old;
                DROP TYPE IF EXISTS mp_gender_enum;
                ALTER TYPE mp_gender_enum_old RENAME TO mp_gender_enum;
              EXCEPTION WHEN others THEN NULL; END;
            END $$;
            """
        )
