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

void ResultTab::set_caption(QString caption) {
  ui->lbl_caption->setText(caption);
}
