package com.pmq.vnnewsvoice.article.messaging;

import com.pmq.vnnewsvoice.article.config.RabbitMQConfig;
import com.pmq.vnnewsvoice.article.dto.amqp.VideoGenerationMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;

/**
 * Publishes a {@link VideoGenerationMessage} to queue {@code ml.video.tasks} via the default
 * exchange (routing key == queue name).
 *
 * <p>MLWorkerService {@code VideoTaskConsumer} will pick up the message, call Veo API (1–3 min) and
 * publish a {@code video.generated} event back via the {@code article.events} fanout.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class VideoGenerationPublisher {

  private final RabbitTemplate rabbitTemplate;

  public void publishVideoTask(VideoGenerationMessage message) {
    // Default exchange: routing key == queue name
    rabbitTemplate.convertAndSend("", RabbitMQConfig.ML_VIDEO_TASKS_QUEUE, message);
    log.info(
        "[AMQP] Published ml.video.tasks: articleId={} style={} duration={}s",
        message.getArticleId(),
        message.getVideoStyle(),
        message.getDurationSeconds());
  }
}
