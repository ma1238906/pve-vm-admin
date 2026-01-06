Based on your requirements and the existing codebase, I have designed a comprehensive implementation plan to build the PVE-VDI system.

The system will consist of a **FastAPI backend** (handling PVE communication, user management, and WebSocket proxying) and a **Vue 3 frontend** (providing Admin and User portals).

## Project Structure Setup
1.  **Backend (`/backend`)**: Python FastAPI application.
2.  **Frontend (`/frontend`)**: Vue 3 + Vite application.

## Implementation Steps

### Phase 1: Backend Initialization & Core Services
1.  **Initialize FastAPI Project**: Set up the directory structure (`app/main.py`, `app/api`, `app/services`, `app/models`).
2.  **Database Integration**: Set up SQLite with SQLAlchemy for managing Users and VM assignments.
3.  **PVE Integration Service**:
    -   Integrate `proxmoxer` library for standard PVE operations (Clone, Start, Stop, Status).
    -   Migrate and refactor the WebSocket proxy logic from `old/app_fastapi_proxy.py` to support noVNC connections securely.
4.  **API Development**:
    -   **Auth**: Login/Register (JWT based).
    -   **VM Management**: APIs to list templates, clone VMs, and manage power states.
    -   **User Management**: APIs to assign VMs to users and set quotas.

### Phase 2: Frontend Initialization & Admin Portal
1.  **Initialize Vue 3 Project**: Use Vite, install `element-plus` (UI library), `pinia` (state management), and `vue-router`.
2.  **Admin Layout**: Create a sidebar navigation layout.
3.  **Dashboard**: Implement the "Resource Monitor" using charts (showing CPU/RAM usage).
4.  **VM Management View**:
    -   Table view of all VMs.
    -   "Clone from Template" wizard.
    -   Resource quota configuration.

### Phase 3: User Portal & noVNC Integration
1.  **User Layout**: A minimalist, clean interface.
2.  **"My Desktop" View**: Card-based layout showing assigned VMs with status indicators (breathing light effect).
3.  **noVNC Integration**:
    -   Implement a secure VNC viewer component.
    -   Connect to the backend WebSocket proxy to stream the desktop.

### Phase 4: Integration & Verification
1.  Connect Frontend to Backend APIs.
2.  Verify the full flow: Admin creates User -> Admin clones VM -> Admin assigns VM to User -> User logs in -> User connects to VM via noVNC.
