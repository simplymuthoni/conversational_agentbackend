# AI Research Assistant

A modern, responsive web application that provides AI-powered research capabilities with real-time activity tracking, comprehensive answers, and source citations.

## 🌟 Features

### Core Functionality
- **Intelligent Research Queries**: Submit complex research questions and receive well-researched, comprehensive answers
- **Real-time Activity Timeline**: Track the research process with timestamped events showing agent progress
- **Source Citations**: Get credible citations with clickable links to original sources
- **Backend Health Monitoring**: Visual indicator showing real-time backend connectivity status
- **Error Handling**: Graceful error messages and recovery for backend failures

### User Experience
- **Dark/Light Mode Toggle**: Seamless theme switching with system preference detection
- **Responsive Design**: Optimized layouts for mobile, tablet, and desktop devices
- **Loading States**: Clear visual feedback during research operations
- **Clean Modern UI**: Soft shadows, rounded corners, and intuitive interface design

## 🛠️ Tech Stack

- **Frontend Framework**: React 18.3.1 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with custom design system
- **UI Components**: Shadcn/ui component library
- **Routing**: React Router DOM
- **State Management**: React hooks (useState, useEffect)
- **Theme Management**: next-themes
- **HTTP Client**: Native Fetch API
- **Form Handling**: React Hook Form with Zod validation
- **Icons**: Lucide React
- **Toast Notifications**: Sonner

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- **Node.js**: Version 16.x or higher
- **npm**: Version 8.x or higher (comes with Node.js)
- **Backend API**: Running instance of the research API (default: `http://localhost:8000`)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <YOUR_GIT_URL>
   cd <YOUR_PROJECT_NAME>
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables** (optional)
   
   Create a `.env` file in the root directory:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

5. **Open your browser**
   
   Navigate to `http://localhost:8080`

## ⚙️ Configuration

### API Endpoints

The application connects to the following backend endpoints (configured in `src/config/api.ts`):

- **Health Check**: `GET /api/health` or `GET /api/status`
- **Research Query**: `POST /api/research`

To change the API base URL, set the `VITE_API_URL` environment variable or update `src/config/api.ts`.

### Health Check Endpoint

By default, the app uses `/api/health`. To switch to `/api/status`, update the `HEALTH_CHECK_ENDPOINT` constant in `src/config/api.ts`:

```typescript
export const HEALTH_CHECK_ENDPOINT = API_ENDPOINTS.status;
```

## 📖 Usage

### Submitting a Research Query

1. Enter your research question in the text area
2. Click the "Ask" button or press Enter
3. Watch the activity timeline populate with research progress
4. Review the comprehensive answer with citations

### Monitoring Backend Status

The header displays a colored indicator:
- 🟢 **Green**: Backend is online and healthy
- 🔴 **Red**: Backend is offline or unreachable
- ⚪ **Gray**: Checking backend status

### Switching Themes

Click the sun/moon icon in the header to toggle between light and dark modes.

## 📁 Project Structure

```
src/
├── components/
│   ├── research/
│   │   ├── Header.tsx           # App header with health status
│   │   ├── ResearchForm.tsx     # Query input form
│   │   ├── Timeline.tsx         # Activity timeline display
│   │   └── AnswerPanel.tsx      # Answer and citations display
│   ├── ui/                      # Shadcn UI components
│   ├── NavLink.tsx              # Navigation link component
│   └── ThemeToggle.tsx          # Theme switcher component
├── hooks/
│   ├── useHealthCheck.ts        # Backend health monitoring hook
│   └── use-toast.ts             # Toast notification hook
├── pages/
│   ├── Index.tsx                # Main research page
│   └── NotFound.tsx             # 404 error page
├── config/
│   └── api.ts                   # API configuration and endpoints
├── lib/
│   └── utils.ts                 # Utility functions
├── App.tsx                      # Root application component
├── main.tsx                     # Application entry point
└── index.css                    # Global styles and design tokens
```

## 🎨 Design System

The application uses a comprehensive design system with semantic tokens defined in `src/index.css`:

- **Colors**: HSL-based color palette with light/dark mode support
- **Typography**: System font stack with consistent sizing
- **Spacing**: Tailwind utility classes
- **Components**: Shadcn UI with custom variants

### Key Design Tokens
- `--background`: Main background color
- `--foreground`: Primary text color
- `--primary`: Brand/accent color
- `--card`: Card background color
- `--border`: Border color
- `--timeline-dot`: Timeline indicator color

## 🔧 Development

### Available Scripts

- `npm run dev` - Start development server (port 8080)
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint

### Development Workflow

1. Make your changes in the appropriate component files
2. The development server will hot-reload your changes
3. Test thoroughly in both light and dark modes
4. Ensure responsive design works on all screen sizes

## 📦 Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### Manual Deployment

The application can be deployed to any static hosting service:
- Vercel
- Netlify
- GitHub Pages
- AWS S3 + CloudFront
- Firebase Hosting

## 🤝 Backend Requirements

This frontend requires a compatible backend API with the following endpoints:

### POST /api/research
Request body:
```json
{
  "query": "Your research question here"
}
```

Response format:
```json
{
  "answer": "Comprehensive research answer...",
  "citations": [
    {
      "url": "https://source1.com",
      "title": "Source Title"
    }
  ],
  "timeline": [
    {
      "id": "evt_1",
      "timestamp": "2024-01-15T10:30:00Z",
      "message": "Started research",
      "type": "info"
    }
  ]
}
```

### GET /api/health
Response format:
```json
{
  "status": "healthy"
}
```

## 🐛 Troubleshooting

### Backend Connection Issues
- Verify the backend is running on `http://localhost:8000`
- Check CORS settings on the backend allow requests from `http://localhost:8080`
- Update `VITE_API_URL` environment variable if using a different backend URL

### Build Errors
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf .vite`
- Ensure Node.js version is 16.x or higher

---

Built with ❤️ 

