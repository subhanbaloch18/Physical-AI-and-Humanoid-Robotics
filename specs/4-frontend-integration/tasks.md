# Tasks: RAG Backend-Frontend Integration

**Input**: Design documents from `/specs/4-frontend-integration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Manual testing per plan.md - no automated tests requested

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `my-website/src/components/`, `my-website/src/utils/`
- **Backend**: `backend/` for API and services
- Paths shown follow the plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create frontend directory structure per implementation plan in my-website/src/components/ChatBot/
- [x] T002 Initialize frontend dependencies (react, axios) in my-website/package.json
- [x] T003 Create backend directory structure: `backend/models/`, `backend/services/`
- [x] T004 [P] Create `backend/models/__init__.py` with empty module
- [x] T005 [P] Create `backend/services/__init__.py` with empty module

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend API infrastructure that MUST be complete before ANY user story can be tested end-to-end

**CRITICAL**: No end-to-end user story testing can occur until this phase is complete

- [x] T006 [P] Create API service module in my-website/src/utils/api.js for backend communication
- [x] T007 Create text selection utility in my-website/src/utils/text-selection.js
- [x] T008 Create data models in my-website/src/models/ (chat-message.js, query-request.js, query-response.js)
- [x] T009 Create `backend/api.py` with FastAPI app instance and CORS middleware configuration
- [x] T010 [P] Create `backend/models/request.py` with ChatQueryRequest and SelectedTextContext Pydantic models per contracts/chat-api.yaml
- [x] T011 [P] Create `backend/models/response.py` with ChatQueryResponse, Source, SessionResponse, ErrorResponse Pydantic models
- [x] T012 Implement `GET /v1/health` endpoint in `backend/api.py` for health checks
- [x] T013 [P] Create `backend/services/session_service.py` with session creation and storage logic
- [x] T014 Implement `POST /v1/chat/session` endpoint in `backend/api.py` for session creation

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Query via Chatbot UI (Priority: P1)

**Goal**: Enable readers browsing the book website to ask questions through an embedded chatbot UI so they can get instant, contextually relevant answers without leaving the page

**Independent Test**: Open the book website, type a question in the chatbot UI, and receive a relevant response from the RAG backend

### Implementation for User Story 1

- [x] T015 [P] [US1] Create ChatBot component in my-website/src/components/ChatBot/ChatBot.jsx
- [x] T016 [US1] Create ChatWindow component in my-website/src/components/ChatBot/ChatWindow.jsx
- [x] T017 [US1] Create Message component in my-website/src/components/ChatBot/Message.jsx
- [x] T018 [US1] Create InputArea component in my-website/src/components/ChatBot/InputArea.jsx
- [x] T019 [US1] Add chatbot styles in my-website/src/components/ChatBot/styles.css
- [x] T020 [US1] Create `backend/services/rag_service.py` with RAG query function that queries Qdrant and generates responses using Cohere
- [x] T021 [US1] Implement `POST /v1/chat/query` endpoint in `backend/api.py` for processing user queries (basic query without context)
- [x] T022 [US1] Update `my-website/src/utils/api.js` to ensure endpoint URLs match backend (`/v1/chat/query` path)
- [x] T023 [US1] Add input validation and error handling for empty/malformed queries in `backend/api.py` (FR-005)

**Checkpoint**: At this point, User Story 1 should be fully functional - users can type questions and receive responses

---

## Phase 4: User Story 2 - Context-Aware Responses (Priority: P1)

**Goal**: Enable the chatbot to consider selected text when answering questions so that responses are specifically grounded in the content the user is currently viewing

**Independent Test**: Select text on a book page, ask a question, and verify the response specifically addresses the selected content

### Implementation for User Story 2

- [x] T024 [P] [US2] Create TextSelector component in my-website/src/components/TextSelection/TextSelector.jsx
- [x] T025 [US2] Create SelectionIndicator component in my-website/src/components/TextSelection/SelectionIndicator.jsx
- [x] T026 [US2] Update `backend/services/rag_service.py` to accept and use selected text context in query processing
- [x] T027 [US2] Update `POST /v1/chat/query` endpoint in `backend/api.py` to handle `selected_text_context` field
- [x] T028 [US2] Verify `my-website/src/components/ChatBot/ChatBot.jsx` passes selection context to API calls (FR-003, FR-006)
- [x] T029 [US2] Add context length validation (max 5000 chars) in `backend/api.py` to handle edge case of long selections
- [x] T030 [US2] Test automatic query mode detection - verify context is included when text is selected, excluded when not (FR-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - basic queries and context-aware queries

---

## Phase 5: User Story 3 - Full-Book Query Support (Priority: P2)

**Goal**: Allow researchers to ask questions that draw from the entire book content so they can get comprehensive answers that synthesize information across multiple chapters or sections

**Independent Test**: Ask questions that require knowledge from multiple parts of the book and verify comprehensive responses with multiple source citations

### Implementation for User Story 3

- [x] T031 [US3] Update `backend/services/rag_service.py` to support full-book queries with multiple source retrieval
- [x] T032 [US3] Enhance `POST /v1/chat/query` response to include source citations array in `backend/api.py`
- [x] T033 [P] [US3] Update `my-website/src/components/ChatBot/Message.jsx` to render source citations from response
- [x] T034 [US3] Test that full-book queries without selection return comprehensive, multi-source responses
- [x] T035 [US3] Add response metadata (confidence_score, processing_time) to `backend/api.py` response

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Session Management & History

**Purpose**: Complete session persistence and history features (FR-007, FR-009)

- [x] T036 Implement `GET /v1/chat/history` endpoint in `backend/api.py` for retrieving session history
- [x] T037 [P] Verify `my-website/src/utils/session-storage.js` correctly saves and loads chat history
- [x] T038 Verify clear chat functionality in `my-website/src/components/ChatBot/ChatBot.jsx` clears session properly (FR-009)
- [x] T039 Test session persistence - refresh page and verify chat history is preserved (FR-007)

---

## Phase 7: Polish & End-to-End Testing

**Purpose**: Integration improvements and end-to-end validation

- [x] T040 [P] Add request timeout handling (30s) in `my-website/src/utils/api.js`
- [x] T041 [P] Add retry logic for transient API failures in `my-website/src/utils/api.js`
- [x] T042 Test edge case: backend unavailable - verify graceful error message
- [x] T043 Test edge case: rapid-fire queries - verify system handles correctly
- [x] T044 Test edge case: content not in book - verify helpful response
- [x] T045 Verify page load time increase is < 1 second with chatbot (SC-005)
- [x] T046 Run quickstart.md validation - verify setup steps work correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS end-to-end testing
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - US1 and US2 are both P1, can run sequentially
  - US3 is P2, should follow US1/US2
- **Session Management (Phase 6)**: Depends on Foundational, can run parallel to user stories
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Independent of US1, but builds on same backend
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Independent but extends rag_service.py

### Within Each User Story

- Backend tasks before frontend verification tasks
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T004, T005 can run in parallel (empty __init__ files)
- T010, T011, T013 can run in parallel (different model/service files)
- T024, T025 already complete and ran in parallel
- T033, T037 can run in parallel (different files)
- T040, T041, T045 can run in parallel (different concerns)

---

## Parallel Example: Foundational Phase

```bash
# Launch all model files together:
Task: "Create backend/models/request.py with ChatQueryRequest and SelectedTextContext Pydantic models"
Task: "Create backend/models/response.py with ChatQueryResponse, Source, SessionResponse, ErrorResponse Pydantic models"
Task: "Create backend/services/session_service.py with session creation and storage logic"
```

## Parallel Example: Polish Phase

```bash
# Launch all error handling improvements together:
Task: "Add request timeout handling (30s) in my-website/src/utils/api.js"
Task: "Add retry logic for transient API failures in my-website/src/utils/api.js"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test basic query functionality
5. Deploy/demo if ready - users can ask questions and get responses

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test independently -> Deploy/Demo (MVP!)
3. Add User Story 2 -> Test context-aware queries -> Deploy/Demo
4. Add User Story 3 -> Test full-book queries -> Deploy/Demo
5. Complete Session Management -> Full persistence
6. Polish -> Production ready

### Task Summary

| Phase | Task Count | Completed | Remaining | Parallel Tasks |
|-------|------------|-----------|-----------|----------------|
| Setup | 5 | 5 | 0 | 2 |
| Foundational | 9 | 9 | 0 | 3 |
| US1 | 9 | 9 | 0 | 0 |
| US2 | 7 | 7 | 0 | 0 |
| US3 | 5 | 5 | 0 | 1 |
| Session | 4 | 4 | 0 | 1 |
| Polish | 7 | 7 | 0 | 3 |
| **Total** | **46** | **46** | **0** | **10** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Many frontend components already exist (marked [x]) - remaining tasks focus on backend and integration
- Backend API is the primary new development work
