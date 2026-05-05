package com.pmq.vnnewsvoice.auth.dto;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class GoogleLoginResponse {
  private String token;

  @JsonIgnore private String refreshToken;

  private GoogleLoginUserResponse user;
}
