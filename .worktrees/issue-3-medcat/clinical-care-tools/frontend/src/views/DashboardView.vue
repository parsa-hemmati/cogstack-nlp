<template>
  <app-layout>
    <v-container fluid>
      <v-row>
        <v-col cols="12">
          <h1 class="text-h3 mb-4">Dashboard</h1>
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="12" md="3">
          <v-card elevation="2">
            <v-card-text>
              <div class="text-h2 text-primary">0</div>
              <div class="text-body-1">Total Patients</div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="3">
          <v-card elevation="2">
            <v-card-text>
              <div class="text-h2 text-success">0</div>
              <div class="text-body-1">Documents Processed</div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="3">
          <v-card elevation="2">
            <v-card-text>
              <div class="text-h2 text-info">0</div>
              <div class="text-body-1">Active Cohorts</div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="3">
          <v-card elevation="2">
            <v-card-text>
              <div class="text-h2 text-warning">0</div>
              <div class="text-body-1">Pending Reviews</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-row class="mt-4">
        <v-col cols="12" md="6">
          <v-card elevation="2">
            <v-card-title>Recent Activity</v-card-title>
            <v-card-text>
              <v-list>
                <v-list-item>
                  <v-list-item-title>No recent activity</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="6">
          <v-card elevation="2">
            <v-card-title>Quick Actions</v-card-title>
            <v-card-text>
              <v-btn block color="primary" class="mb-2" to="/patients">
                <v-icon left>mdi-account-search</v-icon>
                Search Patients
              </v-btn>

              <v-btn block color="secondary" class="mb-2" to="/documents">
                <v-icon left>mdi-file-document</v-icon>
                Upload Documents
              </v-btn>

              <v-btn block color="info" to="/cohort">
                <v-icon left>mdi-database-search</v-icon>
                Build Cohort
              </v-btn>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </app-layout>
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
</script>
