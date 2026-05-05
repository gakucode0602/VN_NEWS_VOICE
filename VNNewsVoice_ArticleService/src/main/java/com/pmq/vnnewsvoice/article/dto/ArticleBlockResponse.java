package com.pmq.vnnewsvoice.article.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ArticleBlockResponse {
  private Long id;
  private Integer orderIndex;
  private String type;
  private String content;
  private String text;
  private String tag;
  private String src;
  private String alt;
  private String caption;
}
