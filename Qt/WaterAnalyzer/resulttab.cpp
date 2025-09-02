#include "resulttab.hpp"
#include "ui_resulttab.h"

ResultTab::ResultTab(QWidget *parent) : QWidget(parent), ui(new Ui::ResultTab) {
  ui->setupUi(this);
}

ResultTab::~ResultTab() { delete ui; }

void ResultTab::set_preview(QPixmap image) {
  ui->lbl_preview->setPixmap(image);
}

uint ResultTab::get_preview_width() { return ui->lbl_preview->width() - 2; }

uint ResultTab::get_preview_height() { return ui->lbl_preview->height() - 2; }

void ResultTab::hide_scale() {
  ui->lbl_scale->hide();
  ui->widget_preview->layout()->removeWidget(ui->lbl_scale);
  ui->widget_preview->layout()->removeWidget(ui->lbl_preview);
  QGridLayout *grid = qobject_cast<QGridLayout *>(ui->widget_preview->layout());
  grid->addWidget(ui->lbl_preview, 1, 0, 1, 2);
}

void ResultTab::set_caption(QString caption) {
  ui->lbl_caption->setText(caption);
}
