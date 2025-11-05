plugins {
    alias(libs.plugins.android.application)
}

android {
    namespace = "com.example.findsouth"
    compileSdk {
        version = release(36)
    }
    
    buildFeatures {
        buildConfig = true
    }

    defaultConfig {
        applicationId = "com.example.findsouth"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        
        // Read server URL from environment variable or local.properties, with fallback
        val serverUrl = project.findProperty("SERVER_URL") as String?
            ?: System.getenv("SERVER_URL")
            ?: "http://192.168.1.101:5173"
        
        buildConfigField("String", "SERVER_URL", "\"$serverUrl\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}

dependencies {
    implementation(libs.appcompat)
    implementation(libs.material)
    implementation(libs.activity)
    implementation(libs.constraintlayout)
    implementation(libs.swiperefreshlayout)
    testImplementation(libs.junit)
    androidTestImplementation(libs.ext.junit)
    androidTestImplementation(libs.espresso.core)
}