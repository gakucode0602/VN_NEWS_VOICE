package com.pmq.vnnewsvoice.comment.messaging;

import com.pmq.vnnewsvoice.comment.config.RabbitMQConfig;
import com.pmq.vnnewsvoice.comment.dto.amqp.UserEventMessage;
import com.pmq.vnnewsvoice.comment.service.CommentService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class UserEventListener {

  private final CommentService commentService;

  @RabbitListener(queues = RabbitMQConfig.USER_EVENTS_COMMENT_QUEUE)
  public void onUserEvent(UserEventMessage event) {
    if (event == null || event.getUserId() == null) {
      log.warn("[AMQP] Skip user.events without userId");
      return;
    }

    String eventType = event.getEventType() != null ? event.getEventType().toLowerCase() : "";

    if ("user.locked".equals(eventType)) {
      int affected = commentService.hideCommentsByUserId(event.getUserId());
      log.info("[AMQP] Hid {} comments for locked user {}", affected, event.getUserId());
      return;
    }

    if ("user.unlocked".equals(eventType)) {
      int affected = commentService.restoreCommentsByUserId(event.getUserId());
      log.info("[AMQP] Restored {} comments for unlocked user {}", affected, event.getUserId());
      return;
    }

    log.debug(
        "[AMQP] Skip unknown user event type: {} for userId={}", eventType, event.getUserId());
  }
}
