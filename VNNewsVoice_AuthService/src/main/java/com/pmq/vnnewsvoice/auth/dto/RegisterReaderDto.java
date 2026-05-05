package com.pmq.vnnewsvoice.auth.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.pmq.vnnewsvoice.auth.validation.StrongPassword;
import java.util.Date;
import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@ToString
public class RegisterReaderDto {
  private Long id;
  private Long userIdId;
  private String userIdUsername;

  @StrongPassword private String userIdPassword;
  private String userIdAvatarUrl;
  private String userIdEmail;

  @JsonFormat(pattern = "yyyy-MM-dd")
  private Date userIdBirthday;

  private String userIdAddress;
  private String userIdPhoneNumber;
  private String userIdGender;
  private Long userIdRoleIdId;
  private String userIdRoleIdName;
  private String userIdAvatarPublicId;
}
