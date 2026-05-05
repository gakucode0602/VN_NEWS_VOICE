package com.pmq.vnnewsvoice.auth.service.impl;

import com.pmq.vnnewsvoice.auth.pojo.Role;
import com.pmq.vnnewsvoice.auth.repository.RoleRepository;
import com.pmq.vnnewsvoice.auth.service.RoleService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class RoleServiceImpl implements RoleService {
  private final RoleRepository roleRepository;

  @Override
  public Role getUserRoleByName(String name) {
    return roleRepository.findFirstByName(name);
  }

  @Override
  public Role getUserRoleById(Long id) {
    if (id == null) {
      return null;
    }
    return roleRepository.findById(id).orElse(null);
  }
}
