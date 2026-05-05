package com.pmq.vnnewsvoice.auth.facade.impl;

import com.pmq.vnnewsvoice.auth.dto.AdminUserDto;
import com.pmq.vnnewsvoice.auth.dto.ApiResult;
import com.pmq.vnnewsvoice.auth.dto.UserListResponse;
import com.pmq.vnnewsvoice.auth.facade.ApiAdminUserFacade;
import com.pmq.vnnewsvoice.auth.pojo.Role;
import com.pmq.vnnewsvoice.auth.pojo.UserInfo;
import com.pmq.vnnewsvoice.auth.service.RoleService;
import com.pmq.vnnewsvoice.auth.service.UserInfoService;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class ApiAdminUserFacadeImpl implements ApiAdminUserFacade {

  private final UserInfoService userInfoService;
  private final RoleService roleService;

  @Override
  public ApiResult<UserListResponse> getUsers(Map<String, String> params) {
    long totalUsers = userInfoService.countSearchUsers(params);
    List<UserInfo> users = userInfoService.getUsers(params);

    List<AdminUserDto> dtos =
        users.stream()
            .map(
                u ->
                    AdminUserDto.builder()
                        .id(u.getId())
                        .username(u.getUsername())
                        .email(u.getEmail())
                        .firstName(u.getFirstName())
                        .lastName(u.getLastName())
                        .phone(u.getPhoneNumber())
                        .roleName(u.getRoleId() != null ? u.getRoleId().getName() : null)
                        .isActive(u.getIsActive())
                        .avatarUrl(u.getAvatarUrl())
                        .createdAt(u.getCreatedAt())
                        .build())
            .collect(Collectors.toList());

    int page = Integer.parseInt(params.getOrDefault("page", "1"));
    int pageSize = Integer.parseInt(params.getOrDefault("pageSize", "10"));
    int totalPages = totalUsers == 0 ? 1 : (int) Math.ceil((double) totalUsers / pageSize);

    UserListResponse res =
        UserListResponse.builder()
            .users(dtos)
            .totalUsers(totalUsers)
            .currentPage(page)
            .totalPages(totalPages)
            .startIndex(dtos.isEmpty() ? 0 : (page - 1) * pageSize + 1)
            .endIndex(Math.min(page * pageSize, (int) totalUsers))
            .build();

    return ApiResult.success(HttpStatus.OK, res);
  }

  @Override
  public ApiResult<Void> toggleUserStatus(Long userId) {
    try {
      boolean rs = userInfoService.toggleUserActive(userId);
      if (rs) {
        return ApiResult.success(HttpStatus.OK, null, "Đã cập nhật trạng thái người dùng");
      }
      return ApiResult.failure(
          HttpStatus.BAD_REQUEST, "Không thể cập nhật trạng thái do lỗi nghiệp vụ");
    } catch (Exception e) {
      return ApiResult.failure(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage());
    }
  }

  @Override
  public ApiResult<Void> updateUserRole(Long userId, String roleName) {
    Optional<UserInfo> userOpt = userInfoService.getUserById(userId);
    if (userOpt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Người dùng không tồn tại");
    }

    Role r = roleService.getUserRoleByName(roleName);
    if (r == null) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Quyền không hợp lệ");
    }

    UserInfo u = userOpt.get();
    u.setRoleId(r);
    try {
      userInfoService.updateUser(u);
      return ApiResult.success(HttpStatus.OK, null, "Đã cập nhật quyền thành công");
    } catch (Exception e) {
      return ApiResult.failure(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage());
    }
  }
}
