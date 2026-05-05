package com.pmq.vnnewsvoice.auth.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.io.Serializable;
import java.util.Date;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class NotificationDto implements Serializable {
  private Long id;
  private String title;
  private String content;
  private Boolean isRead;
  private Date createdAt;
  private Long userId;
}
