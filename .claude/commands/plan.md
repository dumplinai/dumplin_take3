# Feature Planning

Create a new plan to implement the `Feature` using the exact specified markdown `Plan Format`. Follow the `Instructions` to create the plan use the `Relevant Files` to focus on the right files.

## Variables
issue_number: $1

## Instructions

### Planning the Feature
- IMPORTANT: You're writing a plan to implement a net new feature based on the `Feature` that will add value to the application.
- IMPORTANT: The `Feature` describes the feature that will be implemented but remember we're not implementing a new feature, we're creating the plan that will be used to implement the feature based on the `Plan Format` below.
- Create the plan in the `specs/` directory with filename: `feature-planner-{slugified-title}.md`
- Use the `Plan Format` below to create the plan.
- Research the codebase to understand existing patterns, architecture, and conventions before planning the feature.
- IMPORTANT: Replace every <placeholder> in the `Plan Format` with the requested value. Add as much detail as needed to implement the feature successfully.
- Use your reasoning model: THINK HARD about the feature requirements, design, and implementation approach.
- Follow existing patterns and conventions in the codebase. Don't reinvent the wheel.
- Design for extensibility and maintainability.
- Don't use decorators. Keep it simple.
- IMPORTANT: If the feature includes UI components or user interactions:
  - Consider creating integration tests for the Flutter UI
- Respect requested files in the `Relevant Files` section.
- Start your research by reading the `README.md` file. There is a global read me, and then a read me in every subdirectory


## Relevant Files

Focus on the following files:
- `README.md` - Contains the project overview and instructions
- `dumplin_production/dumplin_app/backend/**` - Contains the codebase backend
- `dumplin_production/dumplin_app/frontend/**` - Contains the frontend flutter app for the project
- `dumplin_production/dumplin_app/post_pipeline/**` - Contains the social media post ingestion pipeline used for users to add links to their favorites
- `dumplin_production/Dumplin-ETL/**` - Contains the ETL pipeline that prepares data for the backend

## Plan Format
```md
# Feature: <feature name>

## Feature Description
<describe the feature in detail, including its purpose and value to users>

## Scope
<specify which parts of the codebase will be affected: frontend (Flutter), backend (FastAPI), ETL pipeline, post-processing pipeline, or multiple areas>

## User Story
As a <type of user>
I want to <action/goal>
So that <benefit/value>

## Problem Statement
<clearly define the specific problem or opportunity this feature addresses>

## Solution Statement
<describe the proposed solution approach and how it solves the problem>

## Relevant Files
Use these files to implement the feature:

<find and list the files that are relevant to the feature describe why they are relevant in bullet points. If there are new files that need to be created to implement the feature, list them in an h3 'New Files' section.>

## Implementation Plan
### Phase 1: Foundation
<describe the foundational work needed before implementing the main feature>

### Phase 2: Core Implementation
<describe the main implementation work for the feature>

### Phase 3: Integration
<describe how the feature will integrate with existing functionality>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers plus bullet points. use as many h3 headers as needed to implement the feature. Order matters, start with the foundational shared changes required then move on to the specific implementation. Include creating tests throughout the implementation process.>


## Testing Strategy
### Unit Tests
<describe unit tests needed for the feature>

### Edge Cases
<list edge cases that need to be tested>

## Acceptance Criteria
<list specific, measurable criteria that must be met for the feature to be considered complete>
```


## Report
- Summarize the work you've just done in a concise bullet point list.
- Include the full path to the plan file you created (e.g., `specs/feature-planner-{slugified-title}.md`)

