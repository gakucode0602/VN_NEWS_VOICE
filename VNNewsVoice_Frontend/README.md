<p align="center">
<img src="vnnewsvoice\public\trans_bg.png" width="300px" height="300px">
</p>

# Intelligent News Reading System

The Intelligent News Reading System is designed to enhance the news consumption experience by integrating modern machine learning techniques and large language models. The system collects data from reputable Vietnamese news sources (such as VnExpress, Thanh Niên, Tuổi Trẻ, and Dân Trí) using tools like BeautifulSoup. Leveraging advanced language models (e.g., GPT, Gemini, and ViT5), it automatically summarizes articles and converts them into natural Vietnamese speech. This allows users to quickly grasp key information or listen to the news on the go, which is especially beneficial for busy individuals or those with visual impairments.

# Techs Stack
<p align='center'>
<img src='https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB'/>
<img src='https://img.shields.io/badge/React_Router-CA4245?style=for-the-badge&logo=react-router&logoColor=white'/>
<img src='https://img.shields.io/badge/axios-671ddf?&style=for-the-badge&logo=axios&logoColor=white'/>
<img src='    https://img.shields.io/badge/JavaScript-323330?style=for-the-badge&logo=javascript&logoColor=F7DF1E'/>
<img src='https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white'/>
<img src='https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white'>
<img src='https://img.shields.io/badge/Yarn-2C8EBB?style=for-the-badge&logo=yarn&logoColor=white'/>
<img src='https://img.shields.io/badge/npm-CB3837?style=for-the-badge&logo=npm&logoColor=white'/>
</p>

# Key Features

### 📱 User Interface & Experience
- **Responsive Design**: Fully responsive layout optimized for desktop, tablet, and mobile devices
- **Modern React Architecture**: Built with functional components, hooks, and context API for state management
- **Bootstrap Integration**: Clean, professional UI with Bootstrap components and custom styling

### 🔐 Authentication & User Management
- **JWT Authentication**: Secure token-based authentication system
- **Google OAuth Integration**: Quick login with Google accounts
- **User Profile Management**: Complete profile editing with avatar upload
- **Password Management**: Secure password change functionality
- **Role-Based Access**: Different interface views for Admin, Editor, and Reader roles

### 📰 News Reading Experience
- **Article Browsing**: Clean, card-based article layout with categories
- **Advanced Search**: Real-time search with filters and sorting options
- **Article Detail View**: Full article content with related articles suggestions
- **Bookmarking System**: Save articles for later reading
- **Reading History**: Track user's reading progress and history

### 🎵 Audio Features
- **Text-to-Speech**: Convert articles to natural Vietnamese speech
- **Custom Audio Player**: Built-in audio controls with play, pause, speed adjustment
- **Background Playback**: Continue listening while browsing other articles
- **Audio Quality Settings**: Multiple playback speed options
### 💬 Interactive Features
- **Comment System**: Engage with articles through comments
- **User Interactions**: Like, share, and bookmark articles
- **Notification System**: Real-time updates for user activities
- **Social Features**: Connect and interact with other readers
### ⚡ Performance & Optimization
- **Lazy Loading**: Dynamic component loading for better performance
- **Error Boundaries**: Graceful error handling and fallback UI
- **Loading States**: Smooth loading indicators throughout the app
- **API Caching**: Efficient data fetching and caching strategies

# Installation & Setup
### Prerequisites
- **Node.js 16+** or higher
- **npm** or **yarn** package manager
- **Git/Github**

### Environment Configuration
Create a .env file in the root directory:
```properties
# API Configuration
REACT_APP_BASE_URL=https://your-backend-api.com/api
REACT_APP_API_VERSION=v1

# Google OAuth
REACT_APP_GOOGLE_CLIENT_ID=your_google_client_id_here

# Application Settings
REACT_APP_DEFAULT_LANGUAGE=vi
REACT_APP_ITEMS_PER_PAGE=10
```

### Build & run
```bash
# Clone the repository
git clone https://github.com/your-username/vnnewsvoice-frontend.git
cd vnnewsvoice-frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

# Project structure
```
vnnewsvoice/
├── public/
│   ├── index.html                    # Main HTML template
│   ├── trans_bg_logo.PNG            # Application logo
│   ├── favicon.ico                  # Browser tab icon
│   └── manifest.json               # PWA configuration
│
├── src/
│   ├── components/                  # React Components
│   │   ├── layouts/                # Layout Components
│   │   │   ├── Header.js           # Navigation header
│   │   │   ├── Footer.js           # Site footer
│   │   │   └── MySpinner.js        # Loading spinner
│   │   │
│   │   ├── profile/                # User Profile Components
│   │   │   ├── ProfileInfo.js      # Profile information form
│   │   │   ├── ChangePassword.js   # Password change form
│   │   │   ├── SavedArticle.js     # Bookmarked articles
│   │   │   └── CommentedArticle.js # User comment history
│   │   │
│   │   ├── Home.js                 # Homepage component
│   │   ├── Login.js                # Login page
│   │   ├── Register.js             # Registration page
│   │   ├── Profile.js              # Main profile page
│   │   ├── ArticleDetail.js        # Article reading page
│   │   ├── SearchArticle.js        # Search functionality
│   │   ├── AudioPlayer.js          # Audio playback component
│   │   ├── Comments.js             # Comment system
│   │   ├── RelatedArticles.js      # Article recommendations
│   │   └── RequiredAuth.js         # Authentication wrapper
│   │
│   ├── contexts/                   # React Context
│   │   ├── AppContext.js           # Global app state
│   │   └── SearchContext.js        # Search state management
│   │
│   ├── hooks/                      # Custom React Hooks
│   │   └── userFormValidation.js   # Form validation logic
│   │
│   ├── reducers/                   # State Reducers
│   │   └── userReducer.js          # User state management
│   │
│   ├── configs/                    # Configuration Files
│   │   └── Apis.js                 # API endpoints and axios setup
│   │
│   ├── styles/                     # CSS Stylesheets
│   │   ├── AudioPlayer.css         # Audio player styling
│   │   ├── Footer.css              # Footer styling
│   │   ├── Profile.css             # Profile page styling
│   │   └── RelatedArticles.css     # Related articles styling
│   │
│   ├── App.js                      # Main App component
│   ├── App.css                     # Global app styles
│   ├── index.js                    # Application entry point
│   └── index.css                   # Global CSS variables
│
├── package.json                    # Project dependencies
├── .env                           # Environment variables
├── .gitignore                     # Git ignore rules
└── README.md                      # Project documentation
```

# Support
If you encounter any issues, have questions, or want to contribute, please feel free to:

- Open an [issue](https://github.com/thereaper0602/VNNewsVoice_Backend/issues) in this repository.
- Contact the maintainer via email: **phiminhquang10a10@gmail.com**
- Check the project Wiki or documentation for setup and troubleshooting guides.