package com.pmq.vnnewsvoice.auth.service.impl;

import com.pmq.vnnewsvoice.auth.pojo.Admin;
import com.pmq.vnnewsvoice.auth.repository.AdminRepository;
import com.pmq.vnnewsvoice.auth.service.AdminService;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AdminServiceImpl implements AdminService {
  private final AdminRepository adminRepository;

  @Override
  @Transactional
  public Admin addAdmin(Admin admin) {
    if (admin == null) {
      throw new IllegalArgumentException("Admin cannot be null");
    }
    return adminRepository.save(admin);
  }

  @Override
  public Optional<Admin> getAdminById(Long id) {
    if (id == null || id < 0) {
      return Optional.empty();
    }
    return adminRepository.findById(id);
  }

  @Override
  public Optional<Admin> getAdminByUserId(Long userId) {
    if (userId == null || userId <= 0) {
      return Optional.empty();
    }
    return adminRepository.findByUserId_Id(userId);
  }

  @Override
  @Transactional
  public Admin updateAdmin(Admin admin) {
    if (admin == null || admin.getId() == null) {
      throw new IllegalArgumentException("Admin or Admin ID cannot be null");
    }
    if (!adminRepository.existsById(admin.getId())) {
      return null;
    }
    return adminRepository.save(admin);
  }

  @Override
  @Transactional
  public boolean deleteAdmin(Long id) {
    if (id == null || id <= 0 || !adminRepository.existsById(id)) {
      return false;
    }
    adminRepository.deleteById(id);
    return true;
  }
}
