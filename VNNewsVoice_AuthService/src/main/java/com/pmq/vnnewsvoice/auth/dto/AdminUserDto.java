package com.pmq.vnnewsvoice.auth.dto;

import java.util.Date;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AdminUserDto {
  private Long id;
  private String username;
  private String email;
  private String firstName;
  private String lastName;
  private String phone;
  private String roleName;
  private Boolean isActive;
  private String avatarUrl;
  private Date createdAt;
}
