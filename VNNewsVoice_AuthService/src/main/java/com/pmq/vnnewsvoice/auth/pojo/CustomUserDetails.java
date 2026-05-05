package com.pmq.vnnewsvoice.auth.pojo;

import java.util.Collection;
import java.util.List;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

public class CustomUserDetails implements UserDetails {

  private final UserInfo userInfo;

  public CustomUserDetails(UserInfo userInfo) {
    this.userInfo = userInfo;
  }

  public UserInfo getUserInfo() {
    return userInfo;
  }

  @Override
  public Collection<? extends GrantedAuthority> getAuthorities() {
    return List.of(new SimpleGrantedAuthority(userInfo.getRoleId().getName()));
  }

  @Override
  public String getPassword() {
    return userInfo.getPassword();
  }

  @Override
  public String getUsername() {
    return userInfo.getUsername();
  }

  @Override
  public boolean isAccountNonExpired() {
    return true;
  }

  @Override
  public boolean isAccountNonLocked() {
    return true;
  }

  @Override
  public boolean isCredentialsNonExpired() {
    return true;
  }

  @Override
  public boolean isEnabled() {
    return userInfo.getIsActive() != null ? userInfo.getIsActive() : true;
  }
}
