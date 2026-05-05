import type { ChangeEvent, FormEvent } from "react";
import { useState } from "react";
import { Alert } from "react-bootstrap";
import { useMutation } from "@tanstack/react-query";
import { changePassword } from "../../../services/profile.service";
import type { ApiError, ChangePasswordRequest } from "../../../types";

type ChangePasswordProps = {
  isGoogleUser?: boolean;
};

const ChangePassword = ({ isGoogleUser }: ChangePasswordProps) => {
  const [formData, setFormData] = useState({
    newPassword: "",
    confirmPassword: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const mutation = useMutation<void, ApiError, ChangePasswordRequest>({
    mutationFn: (payload: ChangePasswordRequest) => changePassword(payload),
    onSuccess: () => {
      setSuccess("Đổi mật khẩu thành công!");
      setFormData({ newPassword: "", confirmPassword: "" });
    },
  });

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (formData.newPassword !== formData.confirmPassword) {
      setError("Mật khẩu mới và xác nhận mật khẩu không khớp");
      return;
    }

    try {
      await mutation.mutateAsync({ newPassword: formData.newPassword });
    } catch (err) {
      setError(err?.message || "Đã xảy ra lỗi khi đổi mật khẩu");
    }
  };

  if (isGoogleUser) {
    return (
      <div className="general-info-section">
        <h2>Đổi mật khẩu</h2>
        <Alert variant="info">
          Tài khoản của bạn đăng nhập bằng Google, không thể đổi mật khẩu trực
          tiếp. Để thay đổi mật khẩu, vui lòng truy cập tài khoản Google của bạn.
        </Alert>
      </div>
    );
  }

  return (
    <div className="general-info-section">
      <h2>Đổi mật khẩu</h2>
      {error && <Alert variant="danger">{error}</Alert>}
      {mutation.error && (
        <Alert variant="danger">{mutation.error.message}</Alert>
      )}
      {success && <Alert variant="success">{success}</Alert>}
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-field">
            <label>Mật khẩu mới</label>
            <input
              type="password"
              name="newPassword"
              placeholder="Nhập mật khẩu mới"
              value={formData.newPassword}
              onChange={handleInputChange}
              required
            />
          </div>
          <div className="form-field">
            <label>Xác nhận mật khẩu mới</label>
            <input
              type="password"
              name="confirmPassword"
              placeholder="Xác nhận mật khẩu mới"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              required
            />
          </div>
        </div>

        <div className="save-button-container">
          <button type="submit" className="save-button" disabled={mutation.isPending}>
            {mutation.isPending ? "Đang xử lý..." : "Đổi mật khẩu"}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChangePassword;
