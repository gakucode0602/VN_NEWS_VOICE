import type { ChangeEvent, FormEvent } from "react";

type ProfileFormData = {
  username: string;
  email: string;
  birthday: string;
  gender: string;
  phoneNumber: string;
  address: string;
};

type ProfileInfoProps = {
  formData: ProfileFormData;
  handleInputChange: (
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => void;
  handleSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

const ProfileInfo = ({
  formData,
  handleInputChange,
  handleSubmit,
}: ProfileInfoProps) => {
  return (
    <div className="general-info-section">
      <h2>Thông tin cá nhân</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-field">
            <label>Tên người dùng</label>
            <input
              type="text"
              name="username"
              placeholder="Nhập tên người dùng"
              value={formData.username || ""}
              onChange={handleInputChange}
            />
          </div>
          <div className="form-field">
            <label>Email</label>
            <input
              type="email"
              name="email"
              placeholder="Nhập email"
              value={formData.email || ""}
              disabled={true}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-field">
            <label>Ngày sinh</label>
            <input
              type="date"
              name="birthday"
              value={formData.birthday || ""}
              onChange={handleInputChange}
            />
          </div>
          <div className="form-field">
            <label>Giới tính</label>
            <select
              name="gender"
              value={formData.gender || ""}
              onChange={handleInputChange}
            >
              <option value="">Giới tính</option>
              <option value="Male">Nam</option>
              <option value="Female">Nữ</option>
              <option value="Other">Khác</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-field">
            <label>Số điện thoại</label>
            <input
              type="tel"
              name="phoneNumber"
              placeholder="+12-345 678 910"
              value={formData.phoneNumber || ""}
              onChange={handleInputChange}
            />
          </div>
          <div className="form-field">
            <label>Địa chỉ</label>
            <input
              type="text"
              name="address"
              placeholder="Nhập địa chỉ"
              value={formData.address || ""}
              onChange={handleInputChange}
            />
          </div>
        </div>

        <div className="save-button-container">
          <button type="submit" className="save-button">Lưu</button>
        </div>
      </form>
    </div>
  );
};

export default ProfileInfo;
