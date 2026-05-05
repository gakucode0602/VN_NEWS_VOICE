package com.pmq.vnnewsvoice.comment.pojo;

import java.util.Collection;
import java.util.List;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

/**
 * Lightweight principal for CommentService — populated from JWT claims only. No DB lookup: userId,
 * username, and role are extracted directly from the token.
 */
public class CustomUserDetails implements UserDetails {

  private final Long userId;
  private final String username;
  private final String role; // e.g. "ROLE_READER"

  public CustomUserDetails(Long userId, String username, String role) {
    this.userId = userId;
    this.username = username;
    this.role = role;
  }

  public Long getUserId() {
    return userId;
  }

  @Override
  public Collection<? extends GrantedAuthority> getAuthorities() {
    return List.of(new SimpleGrantedAuthority(role));
  }

  @Override
  public String getPassword() {
    return null;
  }

  @Override
  public String getUsername() {
    return username;
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
    return true;
  }
}
