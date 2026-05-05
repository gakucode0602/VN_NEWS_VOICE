package com.pmq.vnnewsvoice.auth.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class UpdateRoleRequest {
  @NotBlank(message = "Role name is required")
  private String roleName; // e.g. "ROLE_ADMIN", "ROLE_READER"
}
