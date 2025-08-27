#include "processpage.hpp"
#include "ui_processpage.h"

ProcessPage::ProcessPage(QWidget *parent)
    : QWidget(parent), ui(new Ui::ProcessPage) {
  ui->setupUi(this);
}

ProcessPage::~ProcessPage() { delete ui; }

void ProcessPage::on_pb_refresh_clicked() {}
