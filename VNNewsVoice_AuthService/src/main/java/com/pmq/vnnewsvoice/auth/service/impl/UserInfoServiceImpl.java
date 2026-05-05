package com.pmq.vnnewsvoice.auth.service.impl;

import com.pmq.vnnewsvoice.auth.helpers.CloudinaryHelper;
import com.pmq.vnnewsvoice.auth.messaging.UserEventsPublisher;
import com.pmq.vnnewsvoice.auth.pojo.UserInfo;
import com.pmq.vnnewsvoice.auth.repository.UserInfoRepository;
import com.pmq.vnnewsvoice.auth.service.UserInfoService;
import java.io.IOException;
import java.util.Map;
import java.util.Optional;
import java.util.logging.Level;
import java.util.logging.Logger;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

@Service
@Transactional
@RequiredArgsConstructor
public class UserInfoServiceImpl implements UserInfoService {
  private static final Logger LOGGER = Logger.getLogger(UserInfoServiceImpl.class.getName());
  private final UserInfoRepository userInfoRepository;
  private final BCryptPasswordEncoder passwordEncoder;
  private final CloudinaryHelper cloudinaryHelper;
  private final UserEventsPublisher userEventsPublisher;

  @Override
  public UserInfo addUser(UserInfo userInfo) throws IOException {
    if (userInfo == null
        || userInfo.getUsername() == null
        || userInfo.getUsername().isEmpty()
        || userInfo.getPassword() == null
        || userInfo.getPassword().isEmpty()) {
      return null;
    }
    userInfo.setIsActive(true);
    userInfo.setPassword(passwordEncoder.encode(userInfo.getPassword()));
    MultipartFile avatarFile = userInfo.getAvatarFile();
    if (avatarFile != null && !avatarFile.isEmpty()) {
      Map<String, String> res = cloudinaryHelper.uploadMultipartFile(avatarFile);
      userInfo.setAvatarUrl(res.get("url"));
      userInfo.setAvatarPublicId(res.get("publicId"));
    }
    return userInfoRepository.save(userInfo);
  }

  @Override
  public Optional<UserInfo> getUserById(Long id) {
    if (id == null || id <= 0) {
      return Optional.empty();
    }
    return userInfoRepository.findById(id);
  }

  @Override
  public Optional<UserInfo> getUserByUsername(String username) {
    if (username == null || username.isEmpty()) {
      return Optional.empty();
    }
    return userInfoRepository.findFirstByUsername(username);
  }

  @Override
  public Optional<UserInfo> getUserByEmail(String email) {
    if (email == null || email.isEmpty()) {
      return Optional.empty();
    }
    return userInfoRepository.findFirstByEmail(email);
  }

  @Override
  public boolean updateUser(UserInfo userInfo) throws Exception {
    Optional<UserInfo> existing = getUserById(userInfo.getId());
    if (existing.isEmpty()) {
      throw new Exception("Lỗi khi cập nhật người dùng");
    }
    UserInfo existingUser = existing.get();
    if (userInfo.getPassword() != null
        && !userInfo.getPassword().isEmpty()
        && !passwordEncoder.matches(userInfo.getPassword(), existingUser.getPassword())
        && !existingUser.getPassword().equals(userInfo.getPassword())) {
      userInfo.setPassword(passwordEncoder.encode(userInfo.getPassword()));
    } else {
      userInfo.setPassword(existingUser.getPassword());
    }
    processUserAvatar(userInfo, existingUser);
    userInfoRepository.save(userInfo);
    return true;
  }

  @Override
  public boolean deleteUser(Long id) throws Exception {
    Optional<UserInfo> userOpt = getUserById(id);
    if (userOpt.isEmpty()) {
      throw new Exception("Không tìm thấy người dùng");
    }
    UserInfo user = userOpt.get();
    if (user.getAvatarPublicId() != null && !user.getAvatarPublicId().isEmpty()) {
      try {
        cloudinaryHelper.deleteFile(user.getAvatarPublicId());
      } catch (IOException e) {
        LOGGER.log(Level.WARNING, "Error deleting avatar for user ID: " + id, e);
      }
    }
    userInfoRepository.deleteById(id);
    return true;
  }

  private void processUserAvatar(UserInfo user, UserInfo existingUser) {
    if (user.getAvatarFile() == null || user.getAvatarFile().isEmpty()) {
      user.setAvatarUrl(existingUser.getAvatarUrl());
      user.setAvatarPublicId(existingUser.getAvatarPublicId());
    } else {
      try {
        Map<String, String> res = cloudinaryHelper.uploadMultipartFile(user.getAvatarFile());
        user.setAvatarUrl(res.get("url"));
        user.setAvatarPublicId(res.get("publicId"));
      } catch (IOException e) {
        LOGGER.log(Level.SEVERE, "Error uploading avatar for user ID: " + user.getId(), e);
        user.setAvatarUrl(existingUser.getAvatarUrl());
        user.setAvatarPublicId(existingUser.getAvatarPublicId());
      }
    }
  }

  @Override
  public java.util.List<UserInfo> getUsers(Map<String, String> params) {
    Specification<UserInfo> spec =
        com.pmq.vnnewsvoice.auth.repository.specification.UserInfoSpecifications.fromFilters(
            params);
    Sort sort = Sort.by(Sort.Direction.DESC, "createdAt");
    return com.pmq.vnnewsvoice.auth.repository.RepositoryPageable.fromParams(params, 10, sort)
        .map(pageable -> userInfoRepository.findAll(spec, pageable).getContent())
        .orElseGet(() -> userInfoRepository.findAll(spec, sort));
  }

  @Override
  public long countSearchUsers(Map<String, String> filters) {
    return userInfoRepository.count(
        com.pmq.vnnewsvoice.auth.repository.specification.UserInfoSpecifications.fromFilters(
            filters));
  }

  @Override
  public boolean toggleUserActive(Long id) throws Exception {
    Optional<UserInfo> userOpt = getUserById(id);
    if (userOpt.isPresent()) {
      UserInfo user = userOpt.get();
      boolean newIsActive = !user.getIsActive();
      user.setIsActive(newIsActive);
      userInfoRepository.save(user);
      if (newIsActive) {
        userEventsPublisher.publishUserUnlocked(id);
      } else {
        userEventsPublisher.publishUserLocked(id);
      }
      return true;
    } else {
      throw new Exception("Không tìm thấy người dùng");
    }
  }
}
