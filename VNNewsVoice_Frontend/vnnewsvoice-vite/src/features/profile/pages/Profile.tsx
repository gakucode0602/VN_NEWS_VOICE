/* eslint-disable react-hooks/set-state-in-effect */
import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";
import { Alert } from "react-bootstrap";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import "../../../styles/Profile.css";
import MySpinner from "../../../components/layouts/MySpinner";
import { getProfile, updateProfile } from "../../../services/profile.service";
import ProfileInfo from "../components/ProfileInfo";
import ChangePassword from "../components/ChangePassword";
import CommentedArticle from "../components/CommentedArticle";
import SavedArticle from "../components/SavedArticle";
import type { ApiError, ReaderProfile } from "../../../types";

const Profile = () => {
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    birthday: "",
    gender: "",
    phoneNumber: "",
    address: "",
    avatar: "" as string | File,
  });
  const [activeTab, setActiveTab] = useState<
    "profile" | "password" | "commented" | "saved"
  >("profile");

  const queryClient = useQueryClient();

  const profileQuery = useQuery<ReaderProfile, ApiError>({
    queryKey: ["profile"],
    queryFn: getProfile,
  });

  const updateMutation = useMutation<void, ApiError, FormData>({
    mutationFn: updateProfile,
    onSuccess: () => {
      setSuccess("Cập nhật thông tin thành công!");
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });

  useEffect(() => {
    if (!profileQuery.data) return;

    const userData = profileQuery.data;
    setFormData({
      username: userData.userIdUsername || "",
      email: userData.userIdEmail || "",
      birthday: userData.userIdBirthday || "",
      gender: userData.userIdGender || "",
      phoneNumber: userData.userIdPhoneNumber || "",
      address: userData.userIdAddress || "",
      avatar: userData.userIdAvatarUrl || "",
    });
  }, [profileQuery.data]);

  const handleInputChange = (
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = event.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleImageChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setSelectedImage(URL.createObjectURL(file));

      setFormData((prev) => ({
        ...prev,
        avatar: file,
      }));
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSuccess(null);

    const formDataToSend = new FormData();
    formDataToSend.append("userIdUsername", formData.username);
    formDataToSend.append("userIdEmail", formData.email);
    formDataToSend.append("userIdBirthday", formData.birthday);
    formDataToSend.append("userIdGender", formData.gender);
    formDataToSend.append("userIdPhoneNumber", formData.phoneNumber);
    formDataToSend.append("userIdAddress", formData.address);

    if (formData.avatar && formData.avatar instanceof File) {
      formDataToSend.append("avatarFile", formData.avatar);
    }

    try {
      await updateMutation.mutateAsync(formDataToSend);
    } catch {
      // Error handled by mutation state
    }
  };

  const isGoogleUser = profileQuery.data?.userProviders?.some(
    (provider) => provider.providerType === "GOOGLE"
  );

  const renderActiveComponent = () => {
    switch (activeTab) {
      case "profile":
        return (
          <ProfileInfo
            formData={formData}
            handleInputChange={handleInputChange}
            handleSubmit={handleSubmit}
          />
        );
      case "password":
        return <ChangePassword isGoogleUser={isGoogleUser} />;
      case "commented":
        return <CommentedArticle />;
      case "saved":
        return <SavedArticle />;
      default:
        return (
          <ProfileInfo
            formData={formData}
            handleInputChange={handleInputChange}
            handleSubmit={handleSubmit}
          />
        );
    }
  };

  if (profileQuery.isLoading) {
    return <MySpinner />;
  }

  return (
    <div className="profile-container">
      {profileQuery.error && (
        <Alert variant="danger">{profileQuery.error.message}</Alert>
      )}
      {updateMutation.error && (
        <Alert variant="danger">{updateMutation.error.message}</Alert>
      )}
      {success && <Alert variant="success">{success}</Alert>}
      <div className="profile-card">
        {renderActiveComponent()}

        <div className="profile-sidebar">
          <div className="profile-review">
            <h2>
              {profileQuery.data?.userIdUsername || formData.username || ""}
            </h2>
          </div>

          <div className="profile-photo-section">
            <h3>Ảnh đại diện</h3>
            <div className="photo-upload">
              <div className="profile-image">
                <img
                  src={
                    selectedImage ||
                    profileQuery.data?.userIdAvatarUrl ||
                    "https://via.placeholder.com/150"
                  }
                  alt="Profile"
                />
              </div>
              <label className="upload-button">
                <span>Choose Image</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageChange}
                  style={{ display: "none" }}
                />
              </label>
              <p className="upload-info">JPG, GIF or PNG. Max size of 800K</p>
            </div>
          </div>

          <div className="profile-menu">
            <ul>
              <li
                className={activeTab === "profile" ? "active" : ""}
                onClick={() => setActiveTab("profile")}
              >
                <i className="fas fa-user"></i> Thông tin cá nhân
              </li>
              <li
                className={activeTab === "password" ? "active" : ""}
                onClick={() => setActiveTab("password")}
              >
                <i className="fas fa-key"></i> Đổi mật khẩu
              </li>
              <li
                className={activeTab === "commented" ? "active" : ""}
                onClick={() => setActiveTab("commented")}
              >
                <i className="fas fa-comments"></i> Bài viết đã bình luận
              </li>
              <li
                className={activeTab === "saved" ? "active" : ""}
                onClick={() => setActiveTab("saved")}
              >
                <i className="fas fa-bookmark"></i> Bài viết đã lưu
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
