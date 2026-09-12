# Injectable Filler 2D Photoreal Simulation Engine

A 2D image engine designed to simulate dermal filler injections at specified facial sites and volumes, producing photorealistic changes in facial volume and contour from a single photograph.

**Priority:** Medium

Supported treatment regions:

- **Lips**
- **Cheeks**
- **Jaw**

The system is designed with separate frontend, computer-vision, controlled deformation, AI refinement, validation, and infrastructure components.

> **Important:** This project is a visualization/simulation system. Its outputs are illustrative and are not a medical diagnosis, treatment recommendation, or guarantee of real-world treatment results.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Project Goals](#project-goals)
- [How the System Works](#how-the-system-works)
- [User Workflow](#user-workflow)
- [Supported Treatment Areas](#supported-treatment-areas)
- [AI and Computer Vision](#ai-and-computer-vision)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Configuration](#environment-configuration)
- [Frontend-to-Backend Integration](#frontend-to-backend-integration)
- [Production Architecture](#production-architecture)
- [Validation and Evaluation](#validation-and-evaluation)
- [Privacy and Security](#privacy-and-security)
- [Development Roadmap](#development-roadmap)
- [Production Requirements](#production-requirements)
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
              +----------+----------+
              |          |          |
              v          v          v
            Lips       Cheeks       Jaw
              |          |          |
              +----------+----------+
                         |
                         v
                    Region Mask
                         |
                         v
              Volume / Intensity Mapping
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
             Final Preview   Retry / Reject
```

### Why this architecture?

A purely generative approach could change unrelated facial features, alter identity, or produce results that are difficult to reproduce.

The controlled pipeline provides explicit control over:

- the treatment region,
- deformation magnitude,
- boundaries,
- protected facial landmarks,
- simulation parameters,
- validation criteria.

AI can then be used as a refinement layer instead of being given unrestricted control over the complete face.

---

## User Workflow

The frontend follows a four-step workflow inspired by modern facial-simulation products:

```text
1. Photo
      ↓
2. Assessment
      ↓
3. Configure
      ↓
4. Preview
```

### 1. Photo

The user provides a facial photograph.

The interface provides:

- image upload
- drag-and-drop support
- photo/take-photo option where supported
- image requirements
- privacy/consent messaging
- validation states
- upload/loading/error states

The eventual production CV pipeline will validate factors such as:

- supported image format
- image resolution
- face presence
- number of faces
- face orientation
- lighting
- occlusion
- landmark confidence
- overall suitability

---

### 2. Assessment

The user provides simulation-related information.

Current UI includes:

#### Age Range

- 18–30
- 30–45
- 45–60
- 60+

#### Primary Zone

- Lips
- Cheeks
- Jaw

#### Filler Experience

- First Time
- Maintenance
- Previous Treatment / Correction

These selections are intended as **simulation configuration/context**, not medical diagnosis or treatment recommendations.

---

### 3. Configure

The user selects the treatment area and simulation parameters.

Supported areas:

- Lips
- Cheeks
- Jaw

The configuration interface is designed around parameters such as:

- treatment zone
- volume
- intensity
- region-specific controls
- optional measurement/dose overlay

The frontend treats these as simulation parameters.

They are **not medical dosage guidance**.

The eventual backend can consume a structured configuration similar to:

```json
{
  "zone": "cheeks",
  "volume": 2.0,
  "intensity": 0.45,
  "meta": {
    "ageRange": "30-45",
    "experience": "first-time"
  }
}
```

The exact production contract can be versioned and refined as the simulation engine is developed.

---

### 4. Preview

The preview stage is designed to display:

- original image
- simulated image
- before/after comparison
- before/after slider
- side-by-side comparison
- selected treatment zone
- simulation parameters
- optional dose/unit overlay
- reconfiguration controls
- export/download actions
- visualization disclaimer



---

## Supported Treatment Areas

The project currently focuses on three regions:

| Region | Simulation Goal |
|---|---|
| **Lips** | Volume enhancement and contour/shape visualization |
| **Cheeks** | Midface/cheek volume enhancement visualization |
| **Jaw** | Lower-face contour and jawline enhancement visualization |

The system is intentionally limited to these three regions for the current project scope.

---

## AI and Computer Vision

AI and computer vision have different responsibilities.

### Computer Vision

Computer vision provides the geometric understanding of the face.

Potential responsibilities include:

- face detection
- facial landmark detection
- face mesh generation
- region identification
- facial masks
- anatomical/identity anchors
- image-quality assessment

A landmark/mesh system such as MediaPipe can provide the facial geometry required by the simulation engine.

---

### Controlled Simulation Engine

The simulation engine is responsible for the actual requested deformation.

Potential techniques to evaluate include:

- Thin Plate Spline (TPS)
- mesh-based warping
- piecewise affine transformation
- landmark-driven deformation
- displacement fields

The final method should be selected through experimentation and quantitative evaluation.

The engine should be:

- deterministic where possible
- parameterized
- region-specific
- reproducible
- constrained by facial landmarks
- protected against non-target deformation

---

### AI Photorealistic Refinement

After controlled deformation, the result may contain visual artifacts such as:

- stretched texture
- blurred skin
- unnatural texture continuity
- visible deformation boundaries
- inconsistent lighting
- unrealistic local appearance

A suitable pretrained image model can be used to refine these artifacts.

Conceptually:

```text
Controlled Deformation
        ↓
Geometrically Modified Image
        ↓
AI Refinement
        ↓
Photorealistic Simulation
```

The AI refinement stage should be constrained to the affected region as much as technically possible.

It should not be allowed to freely regenerate the entire face.

---

### Groq

Groq is considered an optional AI inference/reasoning layer.

Potential uses include:

- vision analysis
- structured image assessment
- classification
- structured JSON generation
- low-latency AI reasoning

Groq is **not** the core facial deformation engine.

The actual simulation remains the responsibility of the computer-vision and deformation pipeline.

---

## Technology Stack

### Frontend

- React
- TypeScript
- Modern component-based architecture
- Responsive UI
- Production-oriented state management

### Backend

- Python
- FastAPI
- REST API
- Validation and orchestration

### Computer Vision

- MediaPipe / facial landmark technology
- OpenCV
- NumPy

### AI / ML

- PyTorch
- Pretrained image/vision models
- Optional vision/reasoning models through Groq

### Image Infrastructure

- Cloudinary or an equivalent image infrastructure service where required
- Temporary/private image handling
- Controlled retention and deletion

### Development / Deployment

- Git
- GitHub
- Docker
- CI/CD
- Production monitoring and logging

---

## Project Structure

Current frontend structure:

```text
src/
├── components/
│   ├── layout/
│   │   ├── AppHeader
│   │   └── InfoStrip
│   │
│   ├── Stepper/
│   │   └── Stepper
│   │
│   ├── PhotoUpload/
│   │   └── PhotoUpload
│   │
│   ├── Assessment/
│   │   └── Assessment
│   │
│   ├── Configuration/
│   │   └── Configuration
│   │
│   ├── SimulationPreview/
│   │   └── SimulationPreview
│   │
│   ├── DoseOverlay/
│   │   └── DoseOverlay
│   │
│   └── common/
│       ├── Button
│       ├── Card
│       ├── Badge
│       └── Toggle
│
├── pages/
│   └── DermalFillerSimulator/
│
├── hooks/
│   └── useSimulatorWizard.ts
│
├── types/
│   └── simulation.ts
│
├── mock/
│   ├── reference data
│   └── mockSimulationResult.ts
│
└── utils/
    └── formatting / derived calculations
```

The exact filenames may evolve as the project develops.

---

## Getting Started

### Prerequisites

Install:

- **Node.js** (LTS recommended)
- **npm**

Verify the installation:

```bash
node --version
npm --version
```

---

### Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <YOUR_PROJECT_DIRECTORY>
```

Replace the placeholders with the actual GitHub repository URL and directory name.

---

### Install Dependencies

```bash
npm install
```

---

### Start the Development Server

```bash
npm run dev
```

Vite will print a local development URL, usually:

```text
http://localhost:5173
```

Open that URL in your browser.

---

### Build for Production

To create a production frontend build:

```bash
npm run build
```

---

### Preview the Production Build

```bash
npm run preview
```

---

