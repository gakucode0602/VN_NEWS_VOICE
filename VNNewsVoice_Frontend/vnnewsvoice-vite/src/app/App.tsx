import { BrowserRouter, Route, Routes } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";

import Header from "../components/layouts/Header";
import CategoryBar from "../components/layouts/CategoryBar";
import Footer from "../components/layouts/Footer";
import Home from "../features/articles/pages/Home";
import ArticleDetail from "../features/articles/pages/ArticleDetail";
import LatestNews from "../features/articles/pages/LatestNews";
import SearchArticle from "../features/articles/pages/SearchArticle";
import Login from "../features/auth/pages/Login";
import Register from "../features/auth/pages/Register";
import RequireAuth from "../features/auth/components/RequireAuth";
import Profile from "../features/profile/pages/Profile";
import ChatPage from "../features/chat/pages/ChatPage";

const App = () => {
  return (
    <BrowserRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Header />
      <CategoryBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/latest" element={<LatestNews />} />
        <Route path="/articles/:id" element={<ArticleDetail />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/search" element={<SearchArticle />} />
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <Profile />
            </RequireAuth>
          }
        />
        <Route
          path="/chat"
          element={
            <RequireAuth>
              <ChatPage />
            </RequireAuth>
          }
        />
      </Routes>
      <Footer />
    </BrowserRouter>
  );
};

export default App;
