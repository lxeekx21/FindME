<template>
  <div class="flex flex-col items-center justify-center min-h-screen text-center p-8">
    <h1 class="text-3xl font-bold mb-6">Missing Persons Portal</h1>
    <p class="text-gray-600 mb-8 max-w-lg">
      Welcome to the community platform where you can view active missing person alerts 
      and share helpful information through comments.
    </p>

    <div class="flex gap-6">
      <NuxtLink
        to="/alerts"
        class="bg-blue-600 text-white px-6 py-3 rounded-lg shadow hover:bg-blue-700 transition"
      >
        View Alerts
      </NuxtLink>

      <NuxtLink
        to="/comments"
        class="bg-green-600 text-white px-6 py-3 rounded-lg shadow hover:bg-green-700 transition"
      >
        Community Comments
      </NuxtLink>
    </div>
  </div>
</template>
