package com.pmq.vnnewsvoice.article.service.impl;

import com.pmq.vnnewsvoice.article.pojo.ArticleBlock;
import com.pmq.vnnewsvoice.article.repository.ArticleBlockRepository;
import com.pmq.vnnewsvoice.article.service.ArticleBlockService;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ArticleBlockServiceImpl implements ArticleBlockService {
  private final ArticleBlockRepository articleBlockRepository;

  @Override
  @Transactional
  public ArticleBlock addArticleBlock(ArticleBlock articleBlock) {
    if (isValidArticleBlock(articleBlock)) {
      return articleBlockRepository.save(articleBlock);
    }
    return null;
  }

  @Override
  @Transactional(readOnly = true)
  public Optional<ArticleBlock> getArticleBlockById(Long id) {
    if (id == null) {
      return Optional.empty();
    }
    return articleBlockRepository.findById(id);
  }

  @Override
  @Transactional(readOnly = true)
  public Optional<ArticleBlock> getArticleBlockByArticleId(UUID articleId) {
    if (articleId == null) {
      return Optional.empty();
    }
    return articleBlockRepository.findFirstByArticleId_Id(articleId);
  }

  @Override
  @Transactional(readOnly = true)
  public Optional<ArticleBlock> getArticleBlockByArticleIdAndBlockId(UUID articleId, Long blockId) {
    if (articleId == null || blockId == null) {
      return Optional.empty();
    }
    return articleBlockRepository.findByArticleId_IdAndId(articleId, blockId);
  }

  @Override
  @Transactional(readOnly = true)
  public Optional<ArticleBlock> getArticleBlockByArticleIdAndBlockType(
      UUID articleId, String blockType) {
    if (articleId == null || blockType == null) {
      return Optional.empty();
    }
    return articleBlockRepository.findFirstByArticleId_IdAndType(articleId, blockType);
  }

  @Override
  @Transactional
  public Optional<ArticleBlock> updateArticleBlock(ArticleBlock articleBlock) {
    if (isValidArticleBlock(articleBlock)
        && articleBlock.getId() != null
        && articleBlockRepository.existsById(articleBlock.getId())) {
      return Optional.of(articleBlockRepository.save(articleBlock));
    }
    return Optional.empty();
  }

  @Override
  @Transactional
  public boolean deleteArticleBlock(Long id) {
    if (id == null || !articleBlockRepository.existsById(id)) {
      return false;
    }
    articleBlockRepository.deleteById(id);
    return true;
  }

  @Override
  @Transactional(readOnly = true)
  public long countArticleBlocks() {
    return articleBlockRepository.count();
  }

  @Override
  @Transactional(readOnly = true)
  public long countArticleBlocksByArticleId(UUID articleId) {
    if (articleId == null) {
      return 0;
    }
    return articleBlockRepository.countByArticleId_Id(articleId);
  }

  @Override
  @Transactional(readOnly = true)
  public long countArticleBlocksByBlockType(String blockType) {
    if (blockType == null) {
      return 0;
    }
    return articleBlockRepository.countByType(blockType);
  }

  @Override
  @Transactional(readOnly = true)
  public long countArticleBlocksByArticleIdAndBlockType(UUID articleId, String blockType) {
    if (articleId == null || blockType == null) {
      return 0;
    }
    return articleBlockRepository.countByArticleId_IdAndType(articleId, blockType);
  }

  @Override
  @Transactional(readOnly = true)
  public List<ArticleBlock> getArticleBlocksByArticleId(UUID articleId) {
    if (articleId == null) {
      return List.of();
    }
    return articleBlockRepository.findByArticleId_IdOrderByOrderIndexAsc(articleId);
  }

  @Override
  @Transactional(readOnly = true)
  public boolean isValidArticleBlock(ArticleBlock articleBlock) {
    if (articleBlock == null) {
      return false;
    }
    if (articleBlock.getArticleId() == null) {
      return false;
    }
    if (articleBlock.getType() == null) {
      return false;
    }
    if ("paragraph".equals(articleBlock.getType())) {
      if (articleBlock.getText() == null && articleBlock.getContent() == null) {
        return false;
      }
    }
    if ("heading".equals(articleBlock.getType())) {
      if (articleBlock.getContent() == null && articleBlock.getText() == null) {
        return false;
      }
    }
    if ("image".equals(articleBlock.getType())) {
      if (articleBlock.getAlt() == null && articleBlock.getSrc() == null) {
        return false;
      }
    }
    return true;
  }
}
