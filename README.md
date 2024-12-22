# Advanced To-Do App with Project Management and Access Control

## Overview
The Advanced To-Do App is a robust task and project management tool designed to help users organize tasks, collaborate, and manage dependencies effectively. The app provides intelligent scheduling and ensures task visibility and secure user access.

## Features

### User Management
- **Secure Registration and Login**: Password encryption.

### Project Management
- **Project Creation**: Add titles, descriptions, and start dates for projects.
- **Task Management**: Create tasks with nested sub-tasks and set visibility (public/private).

### Smart Dependencies
- **Conditional Dependencies**: Define dependencies between tasks (e.g., "Start Task B only after Task A is complete").
- **Logical Conditions**: Support for AND/OR conditions between tasks.

### Collaboration
- **Task Assignment**: Assign tasks to collaborators and track assigned tasks.
- **Public/Private Task Visibility**: Control who can view tasks and projects.

### Intelligent Scheduling
- **Optimized Scheduling**: Uses topological sorting to suggest schedules based on task dependencies and durations.

### Task Completion
- **Completion Rules**: Enforce task/sub-task dependencies for completion.

## Tech Stack
- **Backend**: Django
- **Database**: MySQL
- **APIs**: RESTful APIs
