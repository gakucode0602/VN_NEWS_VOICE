import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { Button, Modal, Form } from "react-bootstrap";
import { Link } from "react-router-dom";
import { FaEye, FaEyeSlash } from "react-icons/fa";
import { GoogleLogin, type CredentialResponse } from "@react-oauth/google";
import useFormValidation from "../../../hooks/userFormValidation";
import MySpinner from "../../../components/layouts/MySpinner";
import { useAuth } from "../auth-context";

type ModalLoginProps = {
  show: boolean;
  onHide: () => void;
};

const ModalLogin = ({ show, onHide }: ModalLoginProps) => {
  const [showPassword, setShowPassword] = useState(false);
  const {
    login,
    loginWithGoogle,
    isLoading,
    error,
    clearError,
    setError,
  } = useAuth();

  const {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    validateForm,
  } = useFormValidation({
    username: "",
    password: "",
  });

  useEffect(() => {
    return () => clearError();
  }, [clearError]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    await login({
      username: values.username,
      password: values.password,
    });
  };

  const handleGoogleLoginSuccess = async (
    credentialResponse: CredentialResponse
  ) => {
    if (!credentialResponse.credential) {
      setError("Thiếu credential từ Google.");
      return;
    }

    await loginWithGoogle(credentialResponse.credential);
  };

  const handleGoogleLoginError = () => {
    setError("Lỗi đăng nhập!! Vui lòng thử lại.");
  };

  return (
    <Modal
      show={show}
      onHide={onHide}
      size="lg"
      aria-labelledby="contained-modal-title-vcenter"
      centered
    >
      <Modal.Header closeButton>
        <Modal.Title id="contained-modal-title-vcenter">
          Đăng nhập
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <div className="alert alert-danger">{error}</div>}
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Tên đăng nhập</Form.Label>
            <Form.Control
              type="text"
              name="username"
              value={values.username}
              onChange={handleChange}
              onBlur={handleBlur}
              isInvalid={Boolean(touched.username && errors.username)}
              disabled={isLoading}
            />
            <Form.Control.Feedback type="invalid">
              {errors.username}
            </Form.Control.Feedback>
          </Form.Group>

          <Form.Group>
            <Form.Label>Mật khẩu</Form.Label>
            <div className="position-relative">
              <Form.Control
                type={showPassword ? "text" : "password"}
                name="password"
                value={values.password}
                onChange={handleChange}
                onBlur={handleBlur}
                isInvalid={Boolean(touched.password && errors.password)}
                disabled={isLoading}
              />
              <Button
                onClick={() => setShowPassword(!showPassword)}
                className="position-absolute end-0 top-50 translate-middle-y text-muted"
                tabIndex={-1}
              >
                {showPassword ? <FaEyeSlash /> : <FaEye />}
              </Button>
              <Form.Control.Feedback type="invalid">
                {errors.password}
              </Form.Control.Feedback>
            </div>
          </Form.Group>

          {isLoading ? (
            <MySpinner />
          ) : (
            <Button type="submit" disabled={isLoading}>
              Đăng nhập
            </Button>
          )}
        </Form>

        <div className="text-center mt-3">
          <p className="mb-3">Hoặc đăng nhập với</p>
          <div className="d-flex justify-content-center">
            <GoogleLogin
              onSuccess={handleGoogleLoginSuccess}
              onError={handleGoogleLoginError}
              useOneTap
              theme="filled_blue"
              text="signin_with"
              shape="circle"
            />
          </div>
        </div>
      </Modal.Body>
      <Modal.Footer>
        <div className="text-center mt-3">
          <p>
            Chưa có tài khoản? <Link to="/register">Đăng ký ngay</Link>
          </p>
        </div>
      </Modal.Footer>
    </Modal>
  );
};

export default ModalLogin;
