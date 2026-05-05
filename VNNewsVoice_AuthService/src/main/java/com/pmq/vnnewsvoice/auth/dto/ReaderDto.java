package com.pmq.vnnewsvoice.auth.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.io.Serializable;
import java.util.Date;
import java.util.List;
import java.util.Map;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class ReaderDto implements Serializable {
  private Long id;
  private Long userIdId;
  private String userIdUsername;
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
  private List<Map<String, String>> userProviders;
}
