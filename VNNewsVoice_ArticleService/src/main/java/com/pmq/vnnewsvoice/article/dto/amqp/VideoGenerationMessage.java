package com.pmq.vnnewsvoice.article.dto.amqp;

import java.util.UUID;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * AMQP message published to queue {@code ml.video.tasks} (default exchange).
 *
 * <p>Consumed by MLWorkerService {@code VideoTaskConsumer} which calls Veo API and publishes {@code
 * video.generated} event back via fanout exchange {@code article.events}.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class VideoGenerationMessage {

  private UUID articleId;
  private String title;
  private String topImageUrl;
  private String summary;
  private String videoStyle; // e.g. "news", "documentary", "tech" — null → MLWorkerService default
  private Integer durationSeconds; // 4 | 6 | 8 — null → MLWorkerService default (8s)
}
