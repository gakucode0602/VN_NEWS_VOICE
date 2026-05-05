package com.pmq.vnnewsvoice.auth.facade;

import com.pmq.vnnewsvoice.auth.dto.ApiResult;
import com.pmq.vnnewsvoice.auth.dto.UserListResponse;
import java.util.Map;

public interface ApiAdminUserFacade {
  ApiResult<UserListResponse> getUsers(Map<String, String> params);

  ApiResult<Void> toggleUserStatus(Long userId);

  ApiResult<Void> updateUserRole(Long userId, String roleName);
}
