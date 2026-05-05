package com.pmq.vnnewsvoice.auth.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class AuthRequest {
  @NotBlank(message = "Username không được để trống!")
  private String username;

  @NotBlank(message = "Password không được để trống!")
  private String password;
}
