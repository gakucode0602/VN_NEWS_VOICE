package com.pmq.vnnewsvoice.auth.messaging;

import com.pmq.vnnewsvoice.auth.config.RabbitMQConfig;
import com.pmq.vnnewsvoice.auth.dto.amqp.UserEventMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class UserEventsPublisher {

  private final RabbitTemplate rabbitTemplate;

  public void publishUserLocked(Long userId) {
    publish(userId, "user.locked");
  }

  public void publishUserUnlocked(Long userId) {
    publish(userId, "user.unlocked");
  }

  private void publish(Long userId, String eventType) {
    try {
      UserEventMessage message = new UserEventMessage(userId, eventType);
      rabbitTemplate.convertAndSend(RabbitMQConfig.USER_EVENTS_EXCHANGE, "", message);
      log.info("[AMQP] Published {} for userId={}", eventType, userId);
    } catch (Exception e) {
      log.error("[AMQP] Failed to publish {} for userId={}: {}", eventType, userId, e.getMessage());
      // Do not rethrow — AMQP failure must not fail the admin operation.
    }
  }
}
