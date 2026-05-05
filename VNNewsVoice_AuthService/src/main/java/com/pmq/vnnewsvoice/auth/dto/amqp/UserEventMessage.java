package com.pmq.vnnewsvoice.auth.dto.amqp;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserEventMessage {

  private Long userId;

  /**
   * "user.locked" — account deactivated (isActive = false). "user.unlocked" — account reactivated
   * (isActive = true).
   */
  private String eventType;
}
