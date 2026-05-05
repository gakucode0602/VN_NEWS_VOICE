package com.pmq.vnnewsvoice.article.service;

import com.pmq.vnnewsvoice.article.pojo.ArticleBlock;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ArticleBlockService {
  ArticleBlock addArticleBlock(ArticleBlock articleBlock);

  Optional<ArticleBlock> getArticleBlockById(Long id);

  Optional<ArticleBlock> getArticleBlockByArticleId(UUID articleId);

  Optional<ArticleBlock> getArticleBlockByArticleIdAndBlockId(UUID articleId, Long blockId);

  Optional<ArticleBlock> getArticleBlockByArticleIdAndBlockType(UUID articleId, String blockType);

  Optional<ArticleBlock> updateArticleBlock(ArticleBlock articleBlock);

  boolean deleteArticleBlock(Long id);

  long countArticleBlocks();

  long countArticleBlocksByArticleId(UUID articleId);

  long countArticleBlocksByBlockType(String blockType);

  long countArticleBlocksByArticleIdAndBlockType(UUID articleId, String blockType);

  List<ArticleBlock> getArticleBlocksByArticleId(UUID articleId);

  boolean isValidArticleBlock(ArticleBlock articleBlock);
}
