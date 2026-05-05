package com.pmq.vnnewsvoice.comment.dto.amqp;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class UserEventMessage {

  private Long userId;

  /**
   * "user.locked" — user account was deactivated (isActive = false). "user.unlocked" — user account
   * was reactivated (isActive = true).
   */
  private String eventType;
}
