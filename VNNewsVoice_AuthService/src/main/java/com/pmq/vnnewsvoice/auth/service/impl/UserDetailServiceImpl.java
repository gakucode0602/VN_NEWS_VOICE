package com.pmq.vnnewsvoice.auth.service.impl;

import com.pmq.vnnewsvoice.auth.pojo.CustomUserDetails;
import com.pmq.vnnewsvoice.auth.pojo.UserInfo;
import com.pmq.vnnewsvoice.auth.repository.UserInfoRepository;
import com.pmq.vnnewsvoice.auth.service.UserDetailService;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service("userDetailsService")
@Transactional
@RequiredArgsConstructor
public class UserDetailServiceImpl implements UserDetailService {
  private final BCryptPasswordEncoder passwordEncoder;
  private final UserInfoRepository userInfoRepository;

  @Override
  public boolean authenticateUser(String username, String password) {
    Optional<UserInfo> u = userInfoRepository.findFirstByUsername(username);
    if (u.isEmpty()) {
      return false;
    }
    return passwordEncoder.matches(password, u.get().getPassword());
  }

  @Override
  public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
    Optional<UserInfo> u = userInfoRepository.findFirstByUsername(username);
    if (u.isEmpty()) {
      throw new UsernameNotFoundException("Invalid username!");
    }
    return new CustomUserDetails(u.get());
  }
}
