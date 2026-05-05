package com.pmq.vnnewsvoice.auth.service;

import com.pmq.vnnewsvoice.auth.pojo.Role;

public interface RoleService {
  Role getUserRoleByName(String name);

  Role getUserRoleById(Long id);
}
