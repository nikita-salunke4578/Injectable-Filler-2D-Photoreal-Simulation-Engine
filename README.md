# Injectable Filler 2D Photoreal Simulation Engine

A 2D image-based simulation engine designed to visualize controlled facial volume and contour changes at selected facial regions from a single photograph.

The project combines a React/TypeScript frontend with a Python/FastAPI backend and region-specific computer-vision and deformation pipelines for:

- Lips
- Cheeks
- Jaw

The system follows a geometry-first, region-controlled simulation approach, where computer vision determines the treatment region and controlled deformation determines the requested visual change. AI-based refinement is intended to improve photorealism after the geometric transformation.

**Priority:** Medium

> **Important:** This project is a visualization and simulation system. Its outputs are illustrative and are not a medical diagnosis, treatment recommendation, dosage recommendation, or guarantee of real-world treatment results.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Project Goals](#project-goals)
- [Core Design Principles](#core-design-principles)
- [System Architecture](#system-architecture)
- [How the System Works](#how-the-system-works)
- [User Workflow](#user-workflow)
- [Supported Treatment Regions](#supported-treatment-regions)
- [Frontend Architecture](#frontend-architecture)
- [Backend Architecture](#backend-architecture)
- [Shared Backend Infrastructure](#shared-backend-infrastructure)
- [Region-Specific Simulation Modules](#region-specific-simulation-modules)
- [Lips Simulation](#lips-simulation)
- [Cheeks Simulation](#cheeks-simulation)
- [Jaw Simulation](#jaw-simulation)
- [AI and Computer Vision](#ai-and-computer-vision)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Frontend Setup](#frontend-setup)
- [Backend Setup](#backend-setup)
- [Environment Configuration](#environment-configuration)
- [Running the Full Development Environment](#running-the-full-development-environment)
- [Frontend-to-Backend Integration](#frontend-to-backend-integration)
- [Team Development and Ownership](#team-development-and-ownership)
- [Git Workflow](#git-workflow)
- [Privacy and Security](#privacy-and-security)
- [Validation and Evaluation](#validation-and-evaluation)
- [Performance Targets](#performance-targets)
- [Development Roadmap](#development-roadmap)
- [Current Implementation Status](#current-implementation-status)
- [Production Architecture](#production-architecture)
- [Important Notes](#important-notes)
- [License](#license)

---

## Project Overview

The **Injectable Filler 2D Photoreal Simulation Engine** is intended to provide a controlled visual simulation of facial volume enhancement from a single photograph.

The core idea is to combine:

1. **Facial computer vision** to understand the geometry of the face.
2. **Landmark/mesh-based region mapping** to identify treatment areas.
3. **Controlled geometric deformation** to determine exactly what part of the face changes.
4. **AI-based photorealistic refinement** to improve the visual realism of the simulated result.
5. **Identity and non-target validation** to verify that the person's identity is preserved and unrelated facial regions are not unintentionally changed.

The system is intentionally designed so that a generative AI model does **not** independently redesign the patient's face.

The fundamental principle is:

> **The simulation engine controls what changes; AI helps make the change look realistic.**

---

## Project Goals

### Primary Goals

- Simulate filler-related facial volume enhancement from a single photograph.
- Support Lips, Cheeks, and Jaw.
- Provide a professional medical-technology-oriented user experience.
- Preserve the subject's identity.
- Minimize deformation of non-target facial regions.
- Produce visually realistic before/after results.
- Make simulation parameters structured and reproducible.
- Provide measurable output validation.
- Keep the three treatment-region implementations independent.
- Allow multiple team members to develop their respective regions without unnecessarily modifying each other's code.

---

## Core Design Principles

### 1. Geometry First

The requested facial modification should first be determined through explicit computer-vision and geometric deformation logic.

The system should not depend on unrestricted image generation to determine what the face should look like.

---

### 2. Region Isolation

Only the selected treatment region should be modified as much as technically possible.

For example:

```text
Lips Selected
     |
     v
Lip Landmarks
     |
     v
Lip ROI / Mask
     |
     v
Lip Deformation
     |
     v
Refinement
     |
     v
Blending
```

The same principle applies to Cheeks and Jaw.

---

### 3. AI as a Refinement Layer

AI-based image generation or refinement should be applied after controlled geometric deformation.

Preferred architecture:

```text
Facial Geometry
      |
      v
Controlled Deformation
      |
      v
Target Region Mask
      |
      v
AI Refinement
      |
      v
Blending
      |
      v
Validation
```

The AI refinement stage should not freely regenerate the entire face.

---

### 4. Shared Infrastructure

Common functionality should be implemented once and reused by all treatment regions.

Examples include:

- Image loading
- Image validation
- Face detection
- Shared MediaPipe infrastructure
- API schemas
- Configuration
- Cloudinary integration
- Image blending
- Error handling
- Logging

These belong in:

```text
backend/app/common/
```

They should not be duplicated inside the Lips, Cheeks, or Jaw modules.

---

### 5. Region-Specific Ownership

Each treatment region has an isolated backend module:

```text
backend/app/simulations/lips/
backend/app/simulations/cheeks/
backend/app/simulations/jaw/
```

This allows different team members to work independently while sharing the same backend infrastructure.

---

## System Architecture

The repository is divided into two major applications:

```text
Injectable-Filler-2D-Photoreal-Simulation-Engine/
|
├── frontend/
|   └── React + TypeScript application
|
├── backend/
|   └── Python + FastAPI application
|
└── README.md
```

The intended high-level architecture is:

```text
                         User
                           |
                           v
                   React Frontend
                           |
                           v
                 Photo + Configuration
                           |
                           v
                     FastAPI API
                           |
                           v
                Simulation Service
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
           Lips         Cheeks          Jaw
             |             |             |
             +-------------+-------------+
                           |
                           v
                Common Image Utilities
                           |
                           v
                Controlled Deformation
                           |
                           v
                 AI Refinement Layer
                           |
                           v
                     Validation
                           |
                           v
                   Simulation Result
                           |
                           v
                  React Preview
```

---

## How the System Works

The intended end-to-end pipeline is:

```text
                     Patient Photo
                           |
                           v
                   Image Validation
                           |
                           v
                     Face Detection
                           |
                           v
                Facial Landmarks / Mesh
                           |
                           v
                    Region Mapping
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
           Lips         Cheeks          Jaw
             |             |             |
             +-------------+-------------+
                           |
                           v
                       Region Mask
                           |
                           v
                 Volume / Intensity
                       Mapping
                           |
                           v
                Controlled Deformation
                           |
                           v
             Geometrically Modified Image
                           |
                           v
                AI Photorealistic Refinement
                           |
                           v
                  Identity Validation
                           |
                           v
              Non-Target Leakage Validation
                           |
                    +------+------+
                    |             |
                   PASS          FAIL
                    |             |
                    v             v
              Final Preview    Retry / Reject
```

### Why this architecture?

A purely generative approach could change unrelated facial features, alter identity, or produce results that are difficult to reproduce.

The controlled pipeline provides explicit control over:

- Treatment region
- Deformation magnitude
- Boundaries
- Protected facial landmarks
- Simulation parameters
- Validation criteria

AI can then be used as a refinement layer instead of being given unrestricted control over the complete face.

---

## User Workflow

The frontend follows a four-step workflow:

```text
1. Photo
      |
      v
2. Assessment
      |
      v
3. Configure
      |
      v
4. Preview
```

### 1. Photo

The user provides a facial photograph.

The interface provides:

- Image upload
- Drag-and-drop support
- Photo/take-photo option where supported
- Image requirements
- Privacy/consent messaging
- Validation states
- Upload/loading/error states

The eventual production CV pipeline will validate factors such as:

- Supported image format
- Image resolution
- Face presence
- Number of faces
- Face orientation
- Lighting
- Occlusion
- Landmark confidence
- Overall suitability

### 2. Assessment

The user provides simulation-related information.

Current UI includes:

**Age Range**

- 18–30
- 30–45
- 45–60
- 60+

**Primary Zone**

- Lips
- Cheeks
- Jaw

**Filler Experience**

- First Time
- Maintenance
- Previous Treatment / Correction

These selections are intended as simulation configuration/context, not medical diagnosis or treatment recommendations.

### 3. Configure

The user selects the treatment area and simulation parameters.

Supported areas:

- Lips
- Cheeks
- Jaw

The configuration interface currently includes region-specific parameters such as:

- Treatment zone
- Volume
- Intensity-related controls
- Region-specific controls
- Optional measurement/dose overlay

The frontend treats these as simulation parameters.

They are **not medical dosage guidance**.

A conceptual API request may resemble:

```json
{
  "zone": "lips",
  "volume": 1.0,
  "intensity": 0.5,
  "meta": {
    "enhancementLevel": "natural",
    "upperLowerBalance": 0
  }
}
```

The exact production contract can be versioned and refined as the simulation engine is developed.

### 4. Preview

The preview stage is designed to display:

- Original image
- Simulated image
- Before/after comparison
- Before/after slider
- Side-by-side comparison
- Selected treatment zone
- Simulation parameters
- Optional dose/unit overlay
- Reconfiguration controls
- Export/download actions
- Visualization disclaimer

The current frontend uses a mock simulation result while the real simulation backend is being developed.

---

## Supported Treatment Regions

The project currently focuses on three regions:

| Region | Simulation Goal | Ownership |
|---|---|---|
| **Lips** | Volume enhancement and contour/shape visualization | Jayam |
| **Cheeks** | Midface/cheek volume enhancement visualization | Nikita |
| **Jaw** | Lower-face contour and jawline enhancement visualization | Saish |

The system is intentionally limited to these three regions for the current project scope.

---

## Frontend Architecture

The frontend is located in:

```text
frontend/
```

It is implemented using:

- React
- TypeScript
- Vite
- Tailwind CSS

The frontend is responsible for:

- User interface
- Photo upload
- Consent
- Assessment
- Configuration
- Treatment-zone selection
- Simulation parameters
- Wizard navigation
- Preview
- Before/after comparison
- Shared styling

The frontend does not contain the core facial deformation algorithms.

### Shared Frontend Components

The current frontend contains:

```text
frontend/src/components/

├── Assessment/
├── Configuration/
├── DoseOverlay/
├── PhotoUpload/
├── SimulationPreview/
├── Stepper/
├── common/
└── layout/
```

The `Configuration` components are shared between Lips, Cheeks, and Jaw.

Separate React pages for each treatment region are not required.

### Shared Frontend State

The simulation workflow is currently managed through:

```text
frontend/src/hooks/useSimulatorWizard.ts
```

The frontend maintains:

- Current wizard step
- Photo state
- Assessment state
- Configuration state
- Simulation status
- Simulation result
- Simulation errors

### Shared Frontend Types

Shared simulation types are maintained in:

```text
frontend/src/types/simulation.ts
```

These types include:

- Treatment zones
- Assessment state
- Lip parameters
- Cheek parameters
- Jaw parameters
- Configuration state
- Simulation request payload
- Simulation result
- Simulation status

### Shared Frontend Design System

The project's shared styling is maintained in:

```text
frontend/src/index.css
```

This contains the shared:

- Color system
- Typography
- Tailwind theme variables
- Global styles
- Focus states
- Slider styling
- Reduced-motion behavior

Individual treatment modules should not create another global CSS system.

---

## Backend Architecture

The backend is located in:

```text
backend/
```

It is implemented using:

- Python
- FastAPI
- Uvicorn
- Pydantic
- Computer-vision libraries

The backend is responsible for:

- API handling
- Image validation
- Face and landmark processing
- Region-specific simulation
- Image transformation
- AI refinement
- Validation
- Result generation

---

## Shared Backend Infrastructure

Shared backend functionality belongs in:

```text
backend/app/common/
```

The intended structure is:

```text
common/
├── __init__.py
├── config.py
├── schemas.py
├── exceptions.py
├── image_io.py
├── image_validation.py
├── face_detection.py
├── blending.py
├── cloudinary_client.py
└── logging.py
```

### `config.py`

Responsible for application configuration and environment variables.

### `schemas.py`

Contains shared Pydantic models for backend requests and responses.

### `exceptions.py`

Contains shared backend exception types and error-handling structures.

### `image_io.py`

Provides common image operations such as:

- Image decoding
- Image encoding
- NumPy conversion
- Image loading
- Image output preparation

### `image_validation.py`

Responsible for validating uploaded images.

Potential validation includes:

- File type
- File size
- Image readability
- Resolution
- Face presence
- Number of faces
- Image suitability

### `face_detection.py`

Provides shared facial computer-vision infrastructure.

Potential responsibilities include:

- Face detection
- MediaPipe initialization
- Face mesh processing
- Landmark extraction
- Landmark confidence handling

Region-specific landmark selection remains inside the corresponding treatment module.

### `blending.py`

Contains shared image-compositing functionality.

Potential operations include:

- Alpha blending
- Feathered masks
- Seamless blending
- Poisson blending

### `cloudinary_client.py`

Contains shared Cloudinary integration.

Cloudinary is treated as shared image infrastructure rather than part of an individual treatment simulation.

The integration is intended for temporary image handling where required.

### `logging.py`

Provides shared backend logging configuration.

Logs should avoid unnecessary exposure of sensitive image or personal information.

---

## Region-Specific Simulation Modules

Each treatment region has its own isolated module:

```text
backend/app/simulations/

├── lips/
├── cheeks/
└── jaw/
```

This separation is a core part of the project architecture.

---

## Lips Simulation

**Owner: Jayam**

Location:

```text
backend/app/simulations/lips/
```

Structure:

```text
lips/
├── __init__.py
├── pipeline.py
├── landmarks.py
├── mask.py
├── deformation.py
└── refinement.py
```

### `landmarks.py`

Responsible for Lips-specific landmark processing.

The planned Lips implementation uses important lip landmarks including:

```text
61
291
0
17
```

These landmarks can act as important anchors for controlled lip deformation.

### `mask.py`

Responsible for identifying the lip treatment region.

The planned approach includes:

- Lip landmark selection
- Delaunay/convex-hull-based region definition
- Region of interest construction
- Gaussian feathering
- Target-region isolation

### `deformation.py`

Responsible for controlled geometric deformation of the lips.

The planned approach includes:

- Intensity-based displacement
- Landmark movement
- Anatomically constrained displacement
- Thin Plate Spline (TPS)
- Controlled image warping

Conceptually:

```text
Intensity
    |
    v
Displacement Magnitude
    |
    v
Landmark Movement
    |
    v
TPS Transformation
    |
    v
Warped Lips
```

### `refinement.py`

Responsible for optional AI-based refinement after geometric deformation.

Potential responsibilities include:

- Masked image refinement
- Texture restoration
- Artifact reduction
- Local realism improvement

The refinement stage should remain constrained to the affected region.

### `pipeline.py`

Orchestrates the Lips simulation:

```text
Input Image
     |
     v
Landmarks
     |
     v
Lip ROI
     |
     v
Lip Mask
     |
     v
TPS Deformation
     |
     v
AI Refinement
     |
     v
Blending
     |
     v
Result
```

---

## Cheeks Simulation

**Owner: Nikita**

Location:

```text
backend/app/simulations/cheeks/
```

Structure:

```text
cheeks/
├── __init__.py
├── pipeline.py
├── landmarks.py
├── mask.py
├── deformation.py
└── refinement.py
```

The Cheeks module is responsible for:

- Cheek-specific landmarks
- Cheek region mapping
- Cheek ROI
- Mask generation
- Controlled cheek deformation
- Optional AI refinement
- Result generation

Shared infrastructure must remain in:

```text
backend/app/common/
```

---

## Jaw Simulation

**Owner: Saish**

Location:

```text
backend/app/simulations/jaw/
```

Structure:

```text
jaw/
├── __init__.py
├── pipeline.py
├── landmarks.py
├── mask.py
├── deformation.py
└── refinement.py
```

The Jaw module is responsible for:

- Jaw-specific landmarks
- Jaw region mapping
- Jaw ROI
- Mask generation
- Controlled jaw deformation
- Jaw definition control
- Optional AI refinement
- Result generation

Shared infrastructure must remain in:

```text
backend/app/common/
```

---

## AI and Computer Vision

AI and computer vision have different responsibilities.

### Computer Vision

Computer vision provides the geometric understanding of the face.

Potential responsibilities include:

- Face detection
- Facial landmark detection
- Face mesh generation
- Treatment-region identification
- Facial masks
- Anatomical anchors
- Image-quality assessment

The initial computer-vision foundation uses:

- MediaPipe
- OpenCV
- NumPy
- SciPy

### Controlled Geometric Deformation

The simulation engine is responsible for the actual requested deformation.

Potential techniques include:

- Thin Plate Spline (TPS)
- Mesh-based warping
- Piecewise affine transformation
- Landmark-driven deformation
- Displacement fields

The final method should be selected through experimentation and quantitative evaluation.

The engine should be:

- Deterministic where possible
- Parameterized
- Region-specific
- Reproducible
- Constrained by facial landmarks
- Protected against non-target deformation

### AI Photorealistic Refinement

After controlled deformation, the result may contain visual artifacts such as:

- Stretched texture
- Blurred skin
- Unnatural texture continuity
- Visible deformation boundaries
- Inconsistent lighting
- Unrealistic local appearance

A suitable pretrained image model can be used to refine these artifacts.

Conceptually:

```text
Controlled Deformation
        |
        v
Geometrically Modified Image
        |
        v
AI Refinement
        |
        v
Photorealistic Simulation
```

The AI refinement stage should be constrained to the affected region as much as technically possible.

It should not be allowed to freely regenerate the entire face.

### Groq

Groq is considered an optional AI inference/reasoning layer.

Potential uses include:

- Vision analysis
- Structured image assessment
- Classification
- Structured JSON generation
- Low-latency AI reasoning

Groq is **not** the core facial deformation engine.

The actual simulation remains the responsibility of the computer-vision and deformation pipeline.

---

## Technology Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Component-based architecture
- Shared state management

### Backend

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic
- Pydantic Settings

### Computer Vision

- MediaPipe
- OpenCV
- NumPy
- SciPy

### AI / ML

Planned technologies include:

- PyTorch
- Diffusers
- Pretrained image/vision models
- FaceNet-based identity validation
- SSIM
- LPIPS

Optional AI services such as Groq may be evaluated for supporting vision and reasoning tasks.

### Image Infrastructure

Planned:

- Cloudinary or equivalent temporary image infrastructure
- Temporary/private image handling
- Controlled retention and deletion
- Explicit cleanup after processing

### Development and Deployment

Planned:

- Git
- GitHub
- Docker
- CI/CD
- Production logging
- Monitoring

---

## Project Structure

The repository follows this architecture:

```text
Injectable-Filler-2D-Photoreal-Simulation-Engine/
|
├── frontend/
│   ├── public/
│   │
│   ├── src/
│   │   ├── assets/
│   │   │
│   │   ├── components/
│   │   │   ├── Assessment/
│   │   │   ├── Configuration/
│   │   │   ├── DoseOverlay/
│   │   │   ├── PhotoUpload/
│   │   │   ├── SimulationPreview/
│   │   │   ├── Stepper/
│   │   │   ├── common/
│   │   │   └── layout/
│   │   │
│   │   ├── hooks/
│   │   │   └── useSimulatorWizard.ts
│   │   │
│   │   ├── mock/
│   │   │   ├── staticData.ts
│   │   │   └── mockSimulationResult.ts
│   │   │
│   │   ├── pages/
│   │   │   └── DermalFillerSimulator/
│   │   │
│   │   ├── types/
│   │   │   └── simulation.ts
│   │   │
│   │   ├── utils/
│   │   │
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   │
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts
│   └── ...
│
├── backend/
│   │
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── health.py
│   │   │       └── simulation.py
│   │   │
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── schemas.py
│   │   │   ├── exceptions.py
│   │   │   ├── image_io.py
│   │   │   ├── image_validation.py
│   │   │   ├── face_detection.py
│   │   │   ├── blending.py
│   │   │   ├── cloudinary_client.py
│   │   │   └── logging.py
│   │   │
│   │   ├── simulations/
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── lips/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pipeline.py
│   │   │   │   ├── landmarks.py
│   │   │   │   ├── mask.py
│   │   │   │   ├── deformation.py
│   │   │   │   └── refinement.py
│   │   │   │
│   │   │   ├── cheeks/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pipeline.py
│   │   │   │   ├── landmarks.py
│   │   │   │   ├── mask.py
│   │   │   │   ├── deformation.py
│   │   │   │   └── refinement.py
│   │   │   │
│   │   │   └── jaw/
│   │   │       ├── __init__.py
│   │   │       ├── pipeline.py
│   │   │       ├── landmarks.py
│   │   │       ├── mask.py
│   │   │       ├── deformation.py
│   │   │       └── refinement.py
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       └── simulation_service.py
│   │
│   ├── tests/
│   │   ├── common/
│   │   └── simulations/
│   │       └── lips/
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── ...
│
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

Install:

- Node.js LTS
- npm
- Python 3.11 or newer
- Git

Verify the installations:

```bash
node --version
npm --version
python --version
git --version
```

### Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <YOUR_PROJECT_DIRECTORY>
```

Replace the placeholders with the actual GitHub repository URL and directory name.

---

## Frontend Setup

From the repository root:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Vite will normally provide a local development URL similar to:

```text
http://localhost:5173
```

Open the URL in a browser.

### Frontend Production Build

```bash
npm run build
```

### Preview the Production Build

```bash
npm run preview
```

---

## Backend Setup

From the repository root:

```bash
cd backend
```

Create a Python virtual environment.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
pip install -r requirements.txt
```

Start FastAPI:

```powershell
uvicorn app.main:app --reload
```

The backend will normally run at:

```text
http://127.0.0.1:8000
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Backend Health Check

Open:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

FastAPI interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## Environment Configuration

Backend environment configuration is maintained through:

```text
backend/.env
```

A template is provided as:

```text
backend/.env.example
```

Example configuration:

```env
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

ENVIRONMENT=development

MAX_IMAGE_SIZE_MB=10
```

Create the real `.env` file locally when the corresponding infrastructure is implemented.

**Never commit real credentials to GitHub.**

The `.env` file should remain ignored by Git.

---

## Running the Full Development Environment

The frontend and backend should run in separate terminal windows.

### Terminal 1 - Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

### Terminal 2 - Backend

Windows PowerShell:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

The final integrated workflow will connect the frontend to the backend through the simulation API.

---

## Frontend-to-Backend Integration

The current frontend uses a mock simulation function.

Current flow:

```text
Frontend
   |
   v
Configuration
   |
   v
Mock Simulation
   |
   v
Simulation Preview
```

The target production flow is:

```text
React Frontend
      |
      v
Photo + Simulation Configuration
      |
      v
Temporary Image Storage
      |
      v
FastAPI
      |
      v
Simulation Service
      |
      +------> Lips Pipeline
      |
      +------> Cheeks Pipeline
      |
      +------> Jaw Pipeline
      |
      v
Simulation Result
      |
      v
React Preview
```

The existing `mockSimulationResult` implementation is temporary and should eventually be replaced by the real backend API integration.

---

## Team Development and Ownership

The project uses a shared repository with clear ownership boundaries.

### Lips

Owner:

```text
Jayam
```

Primary working directory:

```text
backend/app/simulations/lips/
```

Main files:

```text
pipeline.py
landmarks.py
mask.py
deformation.py
refinement.py
```

### Cheeks

Owner: Nikita

```text
Cheeks Team Member
```

Primary working directory:

```text
backend/app/simulations/cheeks/
```

### Jaw

Owner: Saish

```text
Jaw Team Member
```

Primary working directory:

```text
backend/app/simulations/jaw/
```

### Shared Backend

Shared backend code belongs in:

```text
backend/app/common/
backend/app/api/
backend/app/services/
```

Coordinate with the team before changing shared files.

### Shared Frontend

Frontend UI and state are shared:

```text
frontend/src/components/
frontend/src/hooks/
frontend/src/types/
frontend/src/pages/
frontend/src/index.css
```

Do not create separate copies of the complete frontend for Lips, Cheeks, or Jaw.

The existing shared configuration UI is designed to support all three treatment regions.

---

## Git Workflow

The team currently works on the shared `main` branch.

Before starting work:

```bash
git pull origin main
```

Make changes only in your assigned area whenever possible.

Check your changes:

```bash
git status
```

Add the relevant files:

```bash
git add .
```

Commit:

```bash
git commit -m "Implement lips simulation pipeline"
```

Before pushing, pull the latest changes again:

```bash
git pull origin main
```

Then push:

```bash
git push origin main
```

### Important Rules

1. Always pull before starting work.
2. Avoid modifying another teammate's region.
3. Coordinate before modifying shared files.
4. Keep commits focused.
5. Never commit `.env` files or API credentials.
6. Never commit large model files unless the project explicitly requires it.
7. Test the application before pushing.
8. If two people need to edit the same shared file, coordinate first.

The goal is to keep the shared `main` branch stable without creating unnecessary branch complexity.

---

## Privacy and Security

Facial photographs are sensitive data and should be handled carefully.

The intended production design follows these principles:

- No unnecessary persistent storage of biometric images.
- Images should be processed temporarily.
- Cloudinary or similar infrastructure should be used only where required.
- Temporary uploaded images should be deleted after processing.
- API credentials must remain server-side.
- Secrets must never be committed to GitHub.
- Logs should not contain unnecessary personal or image information.
- Production communication should use HTTPS.
- Access to stored images should be private and controlled.
- Uploaded files should be validated before processing.

The intended privacy model is:

```text
Upload
   |
   v
Temporary Processing
   |
   v
Simulation
   |
   v
Temporary Result
   |
   v
Return Result
   |
   v
Delete Temporary Data
```

The current development implementation does not yet represent the complete production privacy architecture.

---

## Validation and Evaluation

The simulation engine should be evaluated using measurable criteria rather than visual judgment alone.

### 1. Localized Edit Leakage

The amount of unintended modification outside the target region should be minimized.

Target:

```text
Localized Edit Leakage < 5%
```

### 2. Identity Preservation

The generated image should remain sufficiently similar to the original subject.

Target:

```text
FaceNet Cosine Similarity >= 0.90
```

### 3. Structural Similarity

Potential evaluation metrics include:

- SSIM
- LPIPS

These can help measure image similarity and perceptual differences.

### 4. Visual Inspection

Automated metrics should be supplemented with visual evaluation for:

- Natural appearance
- Boundary artifacts
- Texture consistency
- Lighting consistency
- Facial symmetry
- Target-region correctness
- Non-target preservation

---

## Performance Targets

The project targets the following performance goals:

### Geometric Preview

Target:

```text
< 50 ms
```

The geometric preview should ideally be responsive enough for interactive parameter changes.

### AI Refinement

Target:

```text
< 4 seconds
```

The AI refinement stage should ideally complete within a few seconds for a standard input image and selected treatment region.

These are development targets, not current performance guarantees.

Actual performance will depend on:

- Image resolution
- Hardware
- CPU/GPU availability
- Model size
- Inference configuration
- Network latency
- Number of processing steps

---

## Development Roadmap

### Phase 1 - Project Foundation

- [x] React frontend
- [x] Shared frontend components
- [x] Configuration workflow
- [x] Mock simulation
- [x] Frontend/backend separation
- [x] FastAPI backend foundation
- [x] Backend health endpoint
- [x] Region-specific backend directories
- [x] Shared backend directory structure

### Phase 2 - Computer Vision

- [ ] Face detection
- [ ] MediaPipe facial landmarks
- [ ] Landmark validation
- [ ] Face-quality checks
- [ ] Region-specific landmark mapping

### Phase 3 - Region Simulation

#### Lips

- [ ] Lip landmark extraction
- [ ] Lip ROI generation
- [ ] Lip mask generation
- [ ] Gaussian feathering
- [ ] TPS deformation
- [ ] Intensity mapping
- [ ] Poisson/seamless blending
- [ ] Lips refinement

#### Cheeks

- [ ] Cheek landmark extraction
- [ ] Cheek ROI generation
- [ ] Cheek mask generation
- [ ] Controlled deformation
- [ ] Blending
- [ ] Cheek refinement

#### Jaw

- [ ] Jaw landmark extraction
- [ ] Jaw ROI generation
- [ ] Jaw mask generation
- [ ] Controlled deformation
- [ ] Blending
- [ ] Jaw refinement

### Phase 4 - AI Refinement

- [ ] Evaluate suitable pretrained models
- [ ] Implement masked refinement
- [ ] Reduce texture artifacts
- [ ] Preserve identity
- [ ] Validate non-target regions

### Phase 5 - Backend Integration

- [ ] Finalize Pydantic schemas
- [ ] Implement simulation dispatcher
- [ ] Implement `/api/simulate`
- [ ] Connect frontend to FastAPI
- [ ] Add error handling
- [ ] Add processing status
- [ ] Add result handling

### Phase 6 - Image Infrastructure

- [ ] Cloudinary integration
- [ ] Temporary upload handling
- [ ] Temporary result handling
- [ ] Automatic cleanup
- [ ] Secure access controls

### Phase 7 - Validation

- [ ] Leakage evaluation
- [ ] FaceNet identity similarity
- [ ] SSIM evaluation
- [ ] LPIPS evaluation
- [ ] Visual quality evaluation
- [ ] Automated regression tests

### Phase 8 - Production Readiness

- [ ] Docker configuration
- [ ] CI/CD
- [ ] Secure environment management
- [ ] Logging
- [ ] Monitoring
- [ ] Rate limiting
- [ ] HTTPS
- [ ] Production CORS configuration
- [ ] Worker/process management
- [ ] Model optimization

---

## Current Implementation Status

### Completed

- React/TypeScript frontend foundation
- Four-step simulation workflow
- Shared frontend component architecture
- Photo upload interface
- Assessment interface
- Configuration interface
- Lips, Cheeks, and Jaw configuration support
- Shared global CSS/design system
- Frontend state management
- Mock simulation result
- Frontend/backend directory separation
- FastAPI application foundation
- Backend health endpoint
- Shared backend directory structure
- Separate simulation directories for Lips, Cheeks, and Jaw
- Region ownership separation

### In Progress

- Shared backend utilities
- Face detection
- MediaPipe landmark processing
- Region-specific masks
- Geometric deformation
- Lips simulation
- Cheeks simulation
- Jaw simulation
- AI refinement
- API integration
- Cloudinary integration
- Quantitative validation

### Planned

- Production-grade inference pipeline
- Identity preservation evaluation
- Non-target leakage evaluation
- Performance optimization
- Docker deployment
- CI/CD
- Production monitoring

---

## Production Architecture

The intended production architecture is:

```text
                         Client
                           |
                           v
                    React Frontend
                           |
                           v
                    HTTPS / API
                           |
                           v
                     FastAPI API
                           |
                           v
                 Simulation Dispatcher
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
           Lips         Cheeks          Jaw
             |             |             |
             +-------------+-------------+
                           |
                           v
                 Computer Vision Layer
                           |
                           v
                Controlled Deformation
                           |
                           v
                  AI Refinement
                           |
                           v
                     Validation
                           |
                           v
                    Result Service
                           |
                           v
                    Client Preview
```

Temporary image infrastructure can be incorporated around the processing pipeline:

```text
Client
  |
  v
Temporary Image Upload
  |
  v
Backend Processing
  |
  v
Temporary Result
  |
  v
Client
  |
  v
Cleanup
```

Production deployment should use appropriate security, authentication, access control, logging, monitoring, and secret-management practices.

---

## Important Notes

### This is a Simulation

The system is designed for visualization and simulation.

It does not provide:

- Medical diagnosis
- Medical treatment recommendations
- Clinical decision-making
- Individualized medical advice
- Guaranteed real-world treatment outcomes

### Volume Is a Simulation Parameter

Values such as:

```text
0.5 ml
1.0 ml
2.0 ml
```

are simulation inputs within the application.

They should not be interpreted as recommendations for actual injectable filler use.

### AI Limitations

AI-generated or AI-refined images can introduce:

- Anatomical inaccuracies
- Texture artifacts
- Identity changes
- Lighting inconsistencies
- Unexpected modifications

Therefore, AI refinement must remain constrained and should be evaluated quantitatively.

### Development Status

Some technologies and components described in this README are planned architecture rather than fully implemented functionality.

The README should be updated as implementation progresses.

---

## License

No license has been selected for this project yet.

Until a license is added to the repository, the project's source code should not be assumed to be freely reusable, modified, or redistributed.

---
