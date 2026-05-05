package com.pmq.vnnewsvoice.auth.service;

import com.pmq.vnnewsvoice.auth.pojo.UserInfo;
import java.io.IOException;
import java.util.Optional;

public interface UserInfoService {
  UserInfo addUser(UserInfo userInfo) throws IOException;

  Optional<UserInfo> getUserById(Long id);

  Optional<UserInfo> getUserByUsername(String username);

  Optional<UserInfo> getUserByEmail(String email);

  boolean updateUser(UserInfo userInfo) throws Exception;

  boolean deleteUser(Long id) throws Exception;

  java.util.List<UserInfo> getUsers(java.util.Map<String, String> params);

  long countSearchUsers(java.util.Map<String, String> filters);

  boolean toggleUserActive(Long id) throws Exception;
}
