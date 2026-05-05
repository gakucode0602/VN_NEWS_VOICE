package com.pmq.vnnewsvoice.comment.dto.amqp;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class ArticleEventMessage {

  private String articleId;
  private String eventType;
  private String status;
  private Boolean isActive;
}
