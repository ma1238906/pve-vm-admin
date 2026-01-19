# PVE VDI System

This project is a Proxmox VE Virtual Desktop Infrastructure system with a Python FastAPI backend and a Vue 3 frontend.

## Prerequisites

- Python 3.8+
- Node.js 16+
- Proxmox VE Cluster

## Project Structure

- `backend/`: FastAPI application
- `frontend/`: Vue 3 application

## Setup & Run

### Backend

0. 准备python环境（建议使用virtualenv、conda、uv等等）
   
1. Navigate to `backend` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize Database and Create Superuser:
   ```bash
   python create_superuser.py
   ```
   (Default: admin/admin)
4. Run Server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend

1. 从GitHub下载novnc源码放到`frontend/public/novnc/`目录下
   ```bash
   git clone https://github.com/novnc/noVNC.git frontend/public/novnc/
   ```

2. Navigate to `frontend` directory:
   ```bash
   cd frontend
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Run Development Server:
   ```bash
   npm run dev
   ```

## Configuration

复制.env.example为.env并更新Proxmox VE相关配置

## Features

- **Admin Portal**:
    - Dashboard with resource monitoring.
    - VM Management (Clone from template, Start, Stop, Delete).
    - User Management.
- **User Portal**:
    - "My Desktop" view.
    - Integrated noVNC client for browser-based access.
