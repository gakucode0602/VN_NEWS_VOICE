import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { Container, Row, Col, Form, Button, Alert } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";
import { FaEye, FaEyeSlash } from "react-icons/fa";
import MySpinner from "../../../components/layouts/MySpinner";
import useFormValidation from "../../../hooks/userFormValidation";
import { useAuth } from "../auth-context";
import { register as registerRequest } from "../../../services/auth.service";
import type { RegisterFormValues } from "../../../types";

const Register = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);

  const {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    validateForm,
    reset,
  } = useFormValidation<RegisterFormValues>({
    email: "",
    username: "",
    password: "",
    confirmPassword: "",
    phoneNumber: "",
  });

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/");
    }
  }, [isAuthenticated, navigate]);

  const handleRegister = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    if (values.password !== values.confirmPassword) {
      setMessage("Mật khẩu không khớp");
      return;
    }

    try {
      setLoading(true);
      setMessage("");

      const fieldMapping = {
        username: "userIdUsername",
        password: "userIdPassword",
        email: "userIdEmail",
        phoneNumber: "userIdPhoneNumber",
      };

      const formData = new FormData();
      Object.keys(values).forEach((key) => {
        if (key === "confirmPassword") return;
        const mappedKey = fieldMapping[key] || key;
        formData.append(mappedKey, values[key]);
      });

      await registerRequest(formData);
      reset();
      navigate("/login");
    } catch (error) {
      setMessage(error?.message || "Đã xảy ra lỗi khi đăng ký");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container className="my-5">
      <Row className="justify-content-center">
        <Col md={6} lg={5} xl={4}>
          <h2 className="text-center mb-4">Đăng ký</h2>
          {message && <Alert variant="danger">{message}</Alert>}

          <Form onSubmit={handleRegister}>
            <Form.Group className="mb-3">
              <Form.Label>Email</Form.Label>
              <Form.Control
                type="email"
                name="email"
                value={values.email}
                onChange={handleChange}
                onBlur={handleBlur}
                isInvalid={Boolean(touched.email && errors.email)}
                disabled={loading}
              />
              <Form.Control.Feedback type="invalid">
                {errors.email}
              </Form.Control.Feedback>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Tên đăng nhập</Form.Label>
              <Form.Control
                type="text"
                name="username"
                value={values.username}
                onChange={handleChange}
                onBlur={handleBlur}
                isInvalid={Boolean(touched.username && errors.username)}
                disabled={loading}
              />
              <Form.Control.Feedback type="invalid">
                {errors.username}
              </Form.Control.Feedback>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Mật khẩu</Form.Label>
              <div className="position-relative">
                <Form.Control
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={values.password}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  isInvalid={Boolean(touched.password && errors.password)}
                  disabled={loading}
                />
                <Button
                  variant="link"
                  className="position-absolute end-0 top-50 translate-middle-y text-muted"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? <FaEyeSlash /> : <FaEye />}
                </Button>
                <Form.Control.Feedback type="invalid">
                  {errors.password}
                </Form.Control.Feedback>
              </div>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Xác nhận mật khẩu</Form.Label>
              <Form.Control
                type={showPassword ? "text" : "password"}
                name="confirmPassword"
                value={values.confirmPassword}
                onChange={handleChange}
                onBlur={handleBlur}
                isInvalid={Boolean(touched.confirmPassword && errors.confirmPassword)}
                disabled={loading}
              />
              <Form.Control.Feedback type="invalid">
                {errors.confirmPassword}
              </Form.Control.Feedback>
            </Form.Group>

            <Form.Group className="mb-4">
              <Form.Label>Số điện thoại</Form.Label>
              <Form.Control
                type="tel"
                name="phoneNumber"
                value={values.phoneNumber}
                onChange={handleChange}
                onBlur={handleBlur}
                isInvalid={Boolean(touched.phoneNumber && errors.phoneNumber)}
                disabled={loading}
              />
              <Form.Control.Feedback type="invalid">
                {errors.phoneNumber}
              </Form.Control.Feedback>
            </Form.Group>

            {loading ? (
              <MySpinner />
            ) : (
              <div className="d-grid gap-2">
                <Button variant="primary" type="submit">
                  Đăng ký
                </Button>
              </div>
            )}
          </Form>

          <div className="text-center mt-3">
            <p>
              Đã có tài khoản? <Link to="/login">Đăng nhập ngay</Link>
            </p>
          </div>
        </Col>
      </Row>
    </Container>
  );
};

export default Register;
