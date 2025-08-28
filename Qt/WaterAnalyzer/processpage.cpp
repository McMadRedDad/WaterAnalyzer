#include "processpage.hpp"
#include "ui_processpage.h"

ProcessPage::ProcessPage(QWidget *parent)
    : QWidget(parent), ui(new Ui::ProcessPage) {
  ui->setupUi(this);
}

ProcessPage::~ProcessPage() { delete ui; }

void ProcessPage::set_preview(QPixmap image) {
  ui->lbl_preview->setPixmap(image);
}

void ProcessPage::clear_preview() { ui->lbl_preview->clear(); }

void ProcessPage::on_pb_refresh_clicked() {}
