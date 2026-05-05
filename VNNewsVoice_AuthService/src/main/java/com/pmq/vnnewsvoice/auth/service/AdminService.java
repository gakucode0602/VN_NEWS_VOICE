package com.pmq.vnnewsvoice.auth.service;

import com.pmq.vnnewsvoice.auth.pojo.Admin;
import java.util.Optional;

public interface AdminService {
  Admin addAdmin(Admin admin);

  Optional<Admin> getAdminById(Long id);

  Optional<Admin> getAdminByUserId(Long userId);

  Admin updateAdmin(Admin admin);

  boolean deleteAdmin(Long id);
}
