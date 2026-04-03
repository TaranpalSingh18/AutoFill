# Frontend-Backend Authentication Flow - Tech Stack Guide

## 🔧 Technology & Tools Used

### **Frontend (React + Vite)**

#### 1. **axios** - HTTP Client
- **Purpose**: Make API requests to backend
- **Usage**: 
  ```javascript
  import axios from "axios";
  const api = axios.create({ baseURL: API_URL });
  ```
- **Features**: 
  - Automatic JWT token attachment to request headers
  - Auto-logout on 401 (token expired)
  - Error handling & interceptors

#### 2. **React Context API** - State Management
- **Purpose**: Global auth state across entire app
- **File**: `src/context/AuthContext.jsx`
- **What it does**:
  - Stores user, token, loading, error globally
  - No need to pass props down through nested components
  - Initialize from localStorage on app load (persistent login)

#### 3. **Custom Hook - useAuth()**
- **Purpose**: Easy access to auth state from any component
- **Usage**: 
  ```javascript
  const { user, login, logout, isAuthenticated } = useAuth();
  ```
- **File**: `src/hooks/useAuth.js`

#### 4. **localStorage** - Client Storage
- **Purpose**: Persist JWT token & user data across page refreshes
- **Keys stored**:
  - `token` - JWT access token
  - `user` - User object (name, email, id)

#### 5. **React Router** - Navigation
- **Purpose**: Route protection & conditional rendering
- **Used in**:
  - Navbar shows different buttons for authenticated vs non-authenticated users
  - Dashboard link only visible when logged in
  - Login/Signup routes

---

### **Backend (FastAPI + PyJWT + Bcrypt)**

#### 1. **FastAPI** - Web Framework
- **Purpose**: Build REST APIs for auth
- **Endpoints**:
  - `POST /auth/signup` - Register new user
  - `POST /auth/login` - Login with credentials
- **Run**: `python main.py` or `uvicorn main:app --reload`

#### 2. **CORS Middleware**
- **Purpose**: Allow frontend (localhost:5173) to call backend (localhost:8000)
- **Without this**: Browser blocks cross-origin requests
- **Code**:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:5173"],
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

#### 3. **PyJWT (python-jose)** - Token Generation & Validation
- **Purpose**: Create & decode JWT tokens
- **Token contains**: User email (`sub` claim) + expiration time
- **Code**:
  ```python
  access_token = jwt.encode(
      {"sub": email, "exp": expire},
      secret_key,
      algorithm="HS256"
  )
  ```

#### 4. **Bcrypt (passlib)** - Password Hashing
- **Purpose**: Securely hash passwords before storing in DB
- **Never store plaintext passwords!**
- **Code**:
  ```python
  hashed = bcrypt.hash(password)  # Store this
  verify = bcrypt.verify(input_password, hashed)  # Check on login
  ```

#### 5. **MongoDB + PyMongo** - Database
- **Purpose**: Store user data persistently
- **Collections**: `users` collection stores {name, email, password_hash, created_at, is_active}
- **Connection**: Via MONGO_URI in `.env`

#### 6. **Pydantic Models** - Request/Response Validation
- **Purpose**: Validate incoming data from frontend
- **Models**:
  - `Signup(name, email, password)` - Signup request
  - `Login(email, password)` - Login request
- **Auto-generates**: Error messages if fields are missing/invalid

---

## 📊 Data Flow

```
1. User enters email/password in React form
   ↓
2. onClick handleSubmit → calls useAuth.login()
   ↓
3. login() calls authService.login() → HTTP POST /auth/login
   ↓
4. axios interceptor adds JWT token header (if any)
   ↓
5. FastAPI receives request → validates password with bcrypt
   ↓
6. Creates JWT token with jwt.encode()
   ↓
7. Returns { access_token, user_id, name, email }
   ↓
8. Frontend stores in localStorage
   ↓
9. AuthContext updates global state
   ↓
10. Navbar re-renders to show user profile
```

---

## 🔐 Security Features

### **JWT Token Flow**
1. Backend creates token with secret key (never exposed)
2. Frontend receives & stores in localStorage
3. Every API request includes token in `Authorization: Bearer <token>`
4. Backend validates token signature on protected routes

### **Password Security**
1. User submits plaintext password over HTTPS
2. Backend hashes with bcrypt (never reversible)
3. Only hash stored in MongoDB
4. On login: hash(submitted_password) == hash(stored_password)

### **Axios Interceptors**
- Auto-logout if token expires (401 response)
- Redirect to /login automatically

---

## 📁 File Structure

```
Frontend/
├── src/
│   ├── services/
│   │   └── authService.js          # API calls
│   ├── context/
│   │   └── AuthContext.jsx         # Global auth state
│   ├── hooks/
│   │   └── useAuth.js              # Custom hook
│   ├── components/
│   │   ├── Login.jsx               # Updated with auth
│   │   ├── Signup.jsx              # Updated with auth
│   │   └── Navbar.jsx              # Shows user profile
│   └── main.jsx                    # Wrapped with AuthProvider
└── .env.local                      # VITE_API_URL config

Backend/
├── main.py                         # FastAPI app + CORS
├── router/auth/main.py             # Auth endpoints
├── models/auth.py                  # Pydantic models
└── db/database.py                  # MongoDB connection
```

---

## 🚀 Environment Variables

### **Frontend** (`.env.local`)
```
VITE_API_URL=http://localhost:8000
```

### **Backend** (`.env`)
```
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGO=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MONGO_URI=mongodb+srv://...
MONGO_NAME=autofill
```

---

## ✅ What Happens After Login

1. ✅ JWT token stored in localStorage
2. ✅ User object stored in localStorage
3. ✅ AuthContext state updated globally
4. ✅ Navbar shows user name + avatar
5. ✅ Navbar shows "Logout" button (instead of Login/Signup)
6. ✅ Dashboard link appears in navbar
7. ✅ User redirected to `/dashboard`
8. ✅ All future API requests include JWT token automatically

---

## 🔄 Logout Flow

1. User clicks "Logout" button
2. `logout()` clears localStorage (token + user)
3. AuthContext state cleared
4. Navbar re-renders (shows Login/Signup buttons again)
5. User redirected to home

---

## 🐛 Debugging

### **Frontend**
- Open DevTools → Application → localStorage → check `token` and `user`
- Network tab → check if requests include `Authorization: Bearer <token>`

### **Backend**
- Check `.env` has JWT_SECRET_KEY set
- Verify MongoDB connection with `ping_mongo()`
- Test endpoints with Postman/cURL

---

## 📚 Key Concepts Learned

1. **JWT Tokens** - Stateless authentication (no server sessions)
2. **CORS** - Cross-origin resource sharing for frontend-backend communication
3. **Interceptors** - Automatic request/response manipulation in axios
4. **Context API** - Global state without prop drilling
5. **localStorage** - Client-side persistent storage for tokens
6. **Password Hashing** - Bcrypt for secure password storage
7. **Pydantic Validation** - Automatic request validation in FastAPI
