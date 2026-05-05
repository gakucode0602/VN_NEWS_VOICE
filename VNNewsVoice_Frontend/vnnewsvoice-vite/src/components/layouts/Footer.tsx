import { Container, Row, Col } from 'react-bootstrap';
import '../../styles/Footer.css';
import { SiLinkedin, SiGithub, SiGmail } from "react-icons/si";
import { FaPhoneAlt } from "react-icons/fa";

const Footer = () => {
    return (
        <footer className="custom-footer bg-dark text-white pt-5 pb-3">
            <Container>
                <Row>
                    {/* Thông tin ứng dụng */}
                    <Col md={4} className="mb-4">
                        <div className="footer-brand">
                            <div className="d-flex align-items-center mb-3">
                                <img 
                                    src="/trans_bg_logo.PNG" 
                                    alt="VN News Voice Logo" 
                                    className="footer-logo me-3"
                                    style={{ width: '100px', height: '50px' }}
                                />
                                <h5 className="text-uppercase mb-0 fw-bold">VN News Voice</h5>
                            </div>
                            <p className="text-muted">
                                Ứng dụng đọc báo với công nghệ AI hiện đại, 
                                mang đến trải nghiệm đọc tin tức tiện lợi và thông minh.
                            </p>
                            <div className="app-features">
                                <small className="text-muted">
                                    <i className="fas fa-check-circle me-2"></i>Đọc báo bằng giọng nói
                                </small><br />
                                <small className="text-muted">
                                    <i className="fas fa-check-circle me-2"></i>Tóm tắt tin tức thông minh
                                </small><br />
                                <small className="text-muted">
                                    <i className="fas fa-check-circle me-2"></i>Cập nhật tin tức 24/7
                                </small>
                            </div>
                        </div>
                    </Col>

                    {/* Liên kết hữu ích */}
                    <Col md={3} className="mb-4">
                        <h6 className="text-uppercase fw-bold mb-3">Liên kết hữu ích</h6>
                        <ul className="list-unstyled footer-links">
                            <li className="mb-2">
                                <a href="/#" className="text-decoration-none text-muted">
                                    <i className="fas fa-info-circle me-2"></i>Về chúng tôi
                                </a>
                            </li>
                            <li className="mb-2">
                                <a href="/#" className="text-decoration-none text-muted">
                                    <i className="fas fa-shield-alt me-2"></i>Chính sách bảo mật
                                </a>
                            </li>
                            <li className="mb-2">
                                <a href="/#" className="text-decoration-none text-muted">
                                    <i className="fas fa-file-contract me-2"></i>Điều khoản sử dụng
                                </a>
                            </li>
                            <li className="mb-2">
                                <a href="/#" className="text-decoration-none text-muted">
                                    <i className="fas fa-envelope me-2"></i>Liên hệ
                                </a>
                            </li>
                        </ul>
                    </Col>

                    {/* Thông tin nhà phát triển */}
                    <Col md={4} className="mb-4">
                        <h6 className="text-uppercase fw-bold mb-3">Thông tin nhà phát triển</h6>
                        <div className="developer-info">
                            <div className="contact-item mb-2">
                                <i className="fas fa-user me-2 text-primary"></i>
                                <span className="text-muted">Phí Minh Quang - Final Year Student</span>
                            </div>
                            <div className="contact-item mb-2">
                                <i className="fas fa-envelope me-2 text-primary"></i>
                                <a href="mailto:2251012121quang@ou.edu.vn" className="text-decoration-none text-muted">
                                    2251012121quang@ou.edu.vn
                                </a>
                            </div>
                            <div className="contact-item mb-2">
                                <i className="fas fa-phone me-2 text-primary"></i>
                                <a href="tel:+84123456789" className="text-decoration-none text-muted">
                                    (+84) 123-456-789
                                </a>
                            </div>
                            <div className="contact-item mb-3">
                                <i className="fas fa-graduation-cap me-2 text-primary"></i>
                                <span className="text-muted">Trường Đại học Mở Thành Phố Hồ Chí Minh - Khoa CNTT</span>
                            </div>
                        </div>
                    </Col>

                    <Col md={4} className='mb-4'>
                        <h6 className="text-uppercase fw-bold mb-3">Kết nối với tôi</h6>
                        <div className="developer-info">
                                <div className="d-flex gap-3">
                                    <a 
                                        href="https://www.linkedin.com/in/quang-ph%C3%AD-minh-0a9772306/" 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="social-link linkedin"
                                    >
                                        <SiLinkedin />
                                    </a>
                                    <a 
                                        href="https://github.com/thereaper0602" 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="social-link github"
                                    >
                                        <SiGithub />
                                    </a>
                                    <a 
                                        href="mailto:your.email@example.com" 
                                        className="social-link email"
                                    >
                                        <SiGmail />
                                    </a>
                                    <a 
                                        href="tel:+84123456789" 
                                        className="social-link phone"
                                    >
                                        <FaPhoneAlt />
                                    </a>
                                </div>
                            </div>
                    </Col>
                </Row>

                <hr className="my-4" />

                {/* Copyright */}
                <Row>
                    <Col className="text-center">
                        <div className="footer-bottom">
                            <p className="mb-2">
                                © 2025 <strong>VN News Voice</strong>. All rights reserved.
                            </p>
                            <p className="text-muted small mb-0">
                                Developed with <i className="fas fa-heart text-danger"></i> by 
                                <strong> Phí Minh Quang</strong> | Final Year Project
                            </p>
                        </div>
                    </Col>
                </Row>
            </Container>
        </footer>
    );
}

export default Footer;
