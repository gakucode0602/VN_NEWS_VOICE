import { useEffect, useState } from "react";
import Button from "react-bootstrap/Button";
import Container from "react-bootstrap/Container";
import Dropdown from "react-bootstrap/Dropdown";
import Form from "react-bootstrap/Form";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/auth-context";
import { useSearchContext } from "../../contexts/useSearchContext";
import "../../styles/Header.css";

const Header = () => {
  const { searchTerm, setSearchTerm } = useSearchContext();
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchInput, setSearchInput] = useState(searchTerm);

  useEffect(() => {
    setSearchInput(searchTerm);
  }, [searchTerm]);

  const displayName = user?.userIdUsername || "Tài khoản";

  return (
    <header className="main-header">
      <Container>
        <div className="header-inner">
          <div className="header-slot header-left">
            {isAuthenticated ? (
              <Dropdown align="start" className="header-user-dropdown">
                <Dropdown.Toggle variant="light" className="user-toggle">
                  <i className="bi bi-person-circle"></i>
                  <span>{displayName}</span>
                </Dropdown.Toggle>
                <Dropdown.Menu className="user-menu">
                  <Dropdown.Item as={Link} to="/profile">
                    Thông tin cá nhân
                  </Dropdown.Item>
                  <Dropdown.Divider />
                  <Dropdown.Item onClick={logout}>Đăng xuất</Dropdown.Item>
                </Dropdown.Menu>
              </Dropdown>
            ) : (
              <div className="header-auth">
                <Link className="header-auth-link" to="/register">
                  Đăng ký tài khoản
                </Link>
                <Link className="header-auth-link" to="/login">
                  Đăng nhập
                </Link>
              </div>
            )}
          </div>

          <div className="header-slot header-center">
            <Link to="/" className="header-brand">
              <img
                src="/trans_bg_logo.PNG"
                alt="VN News Voice Logo"
                className="header-logo"
              />
              <span className="brand-text">VN News Voice</span>
            </Link>
          </div>

          <div className="header-slot header-right">
            {location.pathname !== "/search" && (
              <Form
                className="header-search"
                onSubmit={(event) => {
                  event.preventDefault();
                  const term = searchInput.trim();
                  if (term) {
                    setSearchTerm(term);
                    navigate("/search");
                  }
                }}
              >
                <Form.Control
                  type="search"
                  placeholder="Tìm kiếm bài viết..."
                  className="header-search-input"
                  aria-label="Search"
                  value={searchInput}
                  onChange={(event) => setSearchInput(event.target.value)}
                />
                <Button
                  variant="light"
                  type="submit"
                  className="header-search-button"
                >
                  <i className="bi bi-search"></i>
                  <span className="visually-hidden">Tìm kiếm</span>
                </Button>
              </Form>
            )}
          </div>
        </div>
      </Container>
    </header>
  );
};

export default Header;
